import itertools
import os
import json
import pickle
from functools import lru_cache
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from sklearn.metrics.pairwise import cosine_similarity
import scipy.sparse as sp

# Load models and dataset at startup
try:
    clf = pickle.load(open("models/nlp_model.pkl", 'rb'))
    vectorizer = pickle.load(open("models/tranform.pkl",'rb'))
    
    movies_dict = pickle.load(open('models/movie_dict.pkl', 'rb'))
    data = pd.DataFrame(movies_dict)
    
    # Pre-normalize sparse vectors at startup for fast dot product later
    raw_matrix = sp.load_npz('models/vectors.npz')
    norms = np.array(raw_matrix.multiply(raw_matrix).sum(axis=1)).flatten() ** 0.5
    norms[norms == 0] = 1  # Avoid division by zero
    similarity_matrix = raw_matrix.multiply(1 / norms[:, np.newaxis])
    similarity_matrix = sp.csr_matrix(similarity_matrix)
    print("Models loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}")

def rcmd(m, tmdb_id=None):
    return _rcmd_cached(m.lower(), int(tmdb_id) if tmdb_id and str(tmdb_id).strip().lower() not in ['','null','undefined','none'] else None)

@lru_cache(maxsize=512)
def _rcmd_cached(m, tmdb_id):
    try:
        # Prefer TMDB ID match for accuracy; fallback to title search
        if tmdb_id is not None:
            if tmdb_id not in data['movie_id'].values:
                return '__NOT_IN_DB__'
            i = data[data['movie_id'] == tmdb_id].index[0]
        else:
            titles_lower = data['title'].str.lower().tolist()
            if m not in titles_lower:
                return '__NOT_IN_DB__'
            i = titles_lower.index(m)

        target_lang = data.iloc[i]['original_language']

        # Fast dot product (pre-normalized at startup = cosine similarity)
        sim_scores = similarity_matrix.dot(similarity_matrix[i].T).toarray().flatten().tolist()
        lst = list(enumerate(sim_scores))

        # Hybrid Scoring: 75% content + 25% popularity
        def calculate_hybrid_score(item):
            try:
                vote = float(data.iloc[item[0]]['vote_average'])
            except:
                vote = 5.0
            return (item[1] * 0.75) + ((vote / 10.0) * 0.25)

        lst = sorted(lst, key=calculate_hybrid_score, reverse=True)
        search_pool = lst[1:500]

        l = []
        # Phase 1: Same-language
        for item in search_pool:
            a = item[0]
            rec_title = data.iloc[a]['title']
            if rec_title.lower() != m and data.iloc[a]['original_language'] == target_lang:
                l.append(rec_title)
            if len(l) == 10:
                break

        # Phase 2: Fill remaining with any language
        if len(l) < 10:
            for item in search_pool:
                rec_title = data.iloc[item[0]]['title']
                if rec_title.lower() != m and rec_title not in l:
                    l.append(rec_title)
                if len(l) == 10:
                    break

        return l
    except Exception as e:
        print("rcmd error: ", e)
        return []

# Converting string like '["abc","def"]' to a proper Python list
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["','')
    my_list[-1] = my_list[-1].replace('"]','')
    return my_list

def get_suggestions():
    try:
        return list(data['title'].str.capitalize())
    except:
        return []

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    suggestions = get_suggestions()
    return render_template('home.html',suggestions=suggestions)

@app.route("/genre")
def genre():
    genre_id = request.args.get('id')
    genre_name = request.args.get('name')
    suggestions = get_suggestions()
    return render_template('genre.html', genre_id=genre_id, genre_name=genre_name, suggestions=suggestions)

@app.route("/similarity",methods=["POST"])
def similarity():
    movie = request.form['name']
    movie_id = request.form.get('movie_id')
    rc = rcmd(movie, movie_id)
    if type(rc)==type('string'):
        return rc
    else:
        m_str="---".join(rc)
        return m_str

TMDB_API_KEY = '5ce2ef2d7c461dea5b4e04900d1c561e'
TMDB_BASE = 'https://api.themoviedb.org/3'
IMG_BASE = 'https://image.tmdb.org/t/p/original'

def tmdb_get(path, params=None):
    """Helper to make a TMDB GET request."""
    try:
        p = {'api_key': TMDB_API_KEY}
        if params:
            p.update(params)
        r = requests.get(f'{TMDB_BASE}/{path}', params=p, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print('TMDB fetch error:', e)
    return None

def fetch_poster_for_title(title):
    """Search TMDB for a rec title and return (poster_url, tmdb_id)."""
    data = tmdb_get('search/movie', {'query': title})
    if not data or not data.get('results'):
        return ('', '')
    best = max(data['results'], key=lambda x: x.get('vote_count', 0))
    poster = IMG_BASE + best['poster_path'] if best.get('poster_path') else ''
    return (poster, best['id'])

def fetch_actor_bio(actor_id):
    """Fetch birthday, biography and place of birth for one actor."""
    data = tmdb_get(f'person/{actor_id}')
    if not data:
        return ('Not Available', 'No biography available.', 'Not Available')
    bday = data.get('birthday', '') or ''
    if bday:
        from datetime import datetime
        try:
            bday = datetime.strptime(bday, '%Y-%m-%d').strftime('%b %d %Y')
        except:
            pass
    bio = data.get('biography') or 'No biography available.'
    place = data.get('place_of_birth') or 'Not Available'
    return (bday or 'Not Available', bio, place)

# Simple in-memory cache for /get_details results
_details_cache = {}

@app.route("/get_details", methods=["POST"])
def get_details():
    payload = request.get_json()
    movie_id   = payload.get('movie_id')
    rec_titles = tuple(payload.get('rec_titles', []))  # make hashable
    not_in_db  = payload.get('not_in_db', False)

    # ── Cache hit: return instantly ──────────────────────────────────────
    cache_key = (movie_id, rec_titles)
    if cache_key in _details_cache:
        return _details_cache[cache_key]

    suggestions = get_suggestions()

    with ThreadPoolExecutor(max_workers=16) as ex:
        # Fire all TMDB calls simultaneously
        fut_movie   = ex.submit(tmdb_get, f'movie/{movie_id}')
        fut_credits = ex.submit(tmdb_get, f'movie/{movie_id}/credits')
        fut_reviews = ex.submit(tmdb_get, f'movie/{movie_id}/reviews')
        fut_posters = {ex.submit(fetch_poster_for_title, t): t for t in rec_titles}

        movie_details = fut_movie.result()
        credits_data  = fut_credits.result()
        reviews_data  = fut_reviews.result()

        # Collect rec posters in order
        poster_results = {}
        for fut, title in fut_posters.items():
            poster_results[title] = fut.result()

    if not movie_details:
        return "Error fetching movie details from TMDB.", 500

    # -- Movie metadata --
    imdb_id      = movie_details.get('imdb_id', '')
    poster       = IMG_BASE + movie_details['poster_path'] if movie_details.get('poster_path') else ''
    overview     = movie_details.get('overview', '')
    vote_average = movie_details.get('vote_average', 0)
    vote_count   = '{:,}'.format(movie_details.get('vote_count', 0))
    release_date = movie_details.get('release_date', '')
    if release_date:
        from datetime import datetime
        try:
            release_date = datetime.strptime(release_date, '%Y-%m-%d').strftime('%b %d %Y')
        except:
            pass
    runtime_min  = movie_details.get('runtime', 0) or 0
    if runtime_min % 60 == 0:
        runtime = f"{runtime_min // 60} hour(s)"
    else:
        runtime = f"{runtime_min // 60} hour(s) {runtime_min % 60} min(s)"
    status       = movie_details.get('status', '')
    genres       = ', '.join(g['name'] for g in movie_details.get('genres', []))
    title        = movie_details.get('title') or movie_details.get('original_title', '')

    # -- Cast (top 10) --
    cast_raw     = (credits_data or {}).get('cast', [])[:10]
    cast_ids     = [str(c['id']) for c in cast_raw]
    cast_names   = [c['name'] for c in cast_raw]
    cast_chars   = [c.get('character', '') for c in cast_raw]
    cast_profiles= [IMG_BASE + c['profile_path'] if c.get('profile_path')
                    else f"https://ui-avatars.com/api/?name={requests.utils.quote(c['name'])}&size=240&background=111&color=fff"
                    for c in cast_raw]

    # -- Actor bios in parallel --
    cast_bdays, cast_bios, cast_places = [], [], []
    with ThreadPoolExecutor(max_workers=10) as ex:
        bio_futs = [ex.submit(fetch_actor_bio, cid) for cid in cast_ids]
        for fut in bio_futs:
            bday, bio, place = fut.result()
            cast_bdays.append(bday)
            cast_bios.append(bio)
            cast_places.append(place)

    # -- Reviews + Sentiment --
    reviews_list, reviews_status = [], []
    for review in (reviews_data or {}).get('results', []):
        text = review.get('content', '')
        if text:
            try:
                vec = vectorizer.transform(np.array([text]))
                pred = clf.predict(vec)
                reviews_status.append('Good' if pred[0] == 1 else 'Bad')
                reviews_list.append(text)
            except Exception as e:
                print('Sentiment error:', e)
    movie_reviews = dict(zip(reviews_list, reviews_status))

    # -- Recommended movie cards --
    rec_movies, rec_poster_urls, rec_ids_list = [], [], []
    for t in rec_titles:
        p_url, p_id = poster_results.get(t, ('', ''))
        rec_movies.append(t)
        rec_poster_urls.append(p_url)
        rec_ids_list.append(p_id)

    movie_cards = {(rec_poster_urls[i], str(rec_ids_list[i])): rec_movies[i]
                   for i in range(len(rec_movies))}
    casts = {cast_names[i]: [cast_ids[i], cast_chars[i], cast_profiles[i]]
             for i in range(len(cast_names))}
    cast_details_dict = {cast_names[i]: [cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]]
                         for i in range(len(cast_names))}

    result = render_template('recommend.html',
        title=title, poster=poster, overview=overview,
        vote_average=vote_average, vote_count=vote_count,
        release_date=release_date, runtime=runtime, status=status,
        genres=genres, movie_cards=movie_cards, reviews=movie_reviews,
        casts=casts, cast_details=cast_details_dict, not_in_db=not_in_db)

    # Store in cache for instant repeat searches
    _details_cache[cache_key] = result
    return result

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False, host="0.0.0.0", port=port)
