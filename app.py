import json
import pickle
import requests
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
    
    # Using sparse vectors + on-the-fly cosine similarity
    similarity_matrix = sp.load_npz('models/vectors.npz')
    print("Models loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}")

def rcmd(m, tmdb_id=None):
    m = m.lower()
    try:
        # Prefer TMDB ID match for accuracy; fallback to title search
        if tmdb_id is not None and str(tmdb_id).strip().lower() not in ["", "null", "undefined", "none"]:
            try:
                tmdb_id_int = int(tmdb_id)
                if tmdb_id_int not in data['movie_id'].values:
                    return('__NOT_IN_DB__')
                else:
                    i = data[data['movie_id'] == tmdb_id_int].index[0]
            except ValueError:
                return('__NOT_IN_DB__')
        else:
            titles_lower = data['title'].str.lower().tolist()
            if m not in titles_lower:
                return('__NOT_IN_DB__')
            else:
                i = titles_lower.index(m)
        
        target_lang = data.iloc[i]['original_language']
        
        # Compute cosine similarity on-the-fly
        sim_scores = cosine_similarity(similarity_matrix[i], similarity_matrix).flatten()
        lst = list(enumerate(sim_scores))
            
        # Enterprise Hybrid Scoring Math
        def calculate_hybrid_score(item):
            movie_index = item[0]
            cosine_sim = item[1]
            
            try:
                vote = float(data.iloc[movie_index]['vote_average'])
            except:
                vote = 5.0
                
            # Hybrid: 75% content similarity + 25% popularity
            hybrid = (cosine_sim * 0.75) + ((vote / 10.0) * 0.25)
            return hybrid
            
        lst = sorted(lst, key=calculate_hybrid_score, reverse=True)
        
        # Top 3000 pool to ensure enough same-language matches
        search_pool = lst[1:3000]
        
        l = []
        # Phase 1: Same-language recommendations
        for item in search_pool:
            a = item[0]
            rec_title = data.iloc[a]['title']
            rec_lang = data.iloc[a]['original_language']
            
            if rec_title.lower() != m and rec_lang == target_lang:
                l.append(rec_title)
            
            if len(l) == 10:
                break
                
        # Phase 2: Fill remaining slots with any language if needed
        if len(l) < 10:
            for item in search_pool:
                a = item[0]
                rec_title = data.iloc[a]['title']
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

@app.route("/recommend",methods=["POST"])
def recommend():
    # getting data from AJAX request
    title = request.form['title']
    cast_ids = request.form['cast_ids']
    cast_names = request.form['cast_names']
    cast_chars = request.form['cast_chars']
    cast_bdays = request.form['cast_bdays']
    cast_bios = request.form['cast_bios']
    cast_places = request.form['cast_places']
    cast_profiles = request.form['cast_profiles']
    imdb_id = request.form['imdb_id']
    poster = request.form['poster']
    genres = request.form['genres']
    overview = request.form['overview']
    vote_average = request.form['rating']
    vote_count = request.form['vote_count']
    release_date = request.form['release_date']
    runtime = request.form['runtime']
    status = request.form['status']
    rec_movies = request.form['rec_movies']
    rec_posters = request.form['rec_posters']
    rec_ids = request.form.get('rec_ids', '[]')
    not_in_db = request.form.get('not_in_db', '0') == '1'

    # get movie suggestions for auto complete
    suggestions = get_suggestions()

    # call the convert_to_list function for every string that needs to be converted to list
    rec_movies = convert_to_list(rec_movies)
    rec_posters = convert_to_list(rec_posters)
    # Parse rec_ids (JSON list of ints/strings)
    try:
        rec_ids_list = json.loads(rec_ids)
    except:
        rec_ids_list = ['' for _ in rec_movies]
    cast_names = convert_to_list(cast_names)
    cast_chars = convert_to_list(cast_chars)
    cast_profiles = convert_to_list(cast_profiles)
    cast_bdays = convert_to_list(cast_bdays)
    cast_bios = convert_to_list(cast_bios)
    cast_places = convert_to_list(cast_places)
    
    # convert string to list (eg. "[1,2,3]" to [1,2,3])
    cast_ids = cast_ids.split(',')
    cast_ids[0] = cast_ids[0].replace("[","")
    cast_ids[-1] = cast_ids[-1].replace("]","")
    
    # rendering the string to python string
    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r'\n', '\n').replace(r'\"','\"')
    
    # Build movie cards dict: (poster, id) -> title
    movie_cards = {(rec_posters[i], str(rec_ids_list[i]) if i < len(rec_ids_list) else ''): rec_movies[i] for i in range(len(rec_posters))}
    
    casts = {cast_names[i]:[cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}

    cast_details = {cast_names[i]:[cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}

    # Fetching reviews from TMDB API
    reviews_list = []
    reviews_status = []
    try:
        tmdb_api_key = '5ce2ef2d7c461dea5b4e04900d1c561e'
        url = 'https://api.themoviedb.org/3/movie/{}/reviews?api_key={}'.format(imdb_id, tmdb_api_key)
        response = requests.get(url)
        if response.status_code == 200:
            reviews_data = response.json()
            for review in reviews_data.get('results', []):
                review_text = review.get('content', '')
                if review_text:
                    try:
                        # passing the review to the model
                        movie_review_list = np.array([review_text])
                        movie_vector = vectorizer.transform(movie_review_list)
                        pred = clf.predict(movie_vector)
                        reviews_status.append('Good' if pred[0] == 1 else 'Bad')
                        reviews_list.append(review_text)
                    except Exception as e:
                        print("Error predicting review sentiment:", e)
    except Exception as e:
        print("Error fetching TMDB reviews:", e)

    # combining reviews into a dictionary
    movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}     

    # passing all the data to the html file
    return render_template('recommend.html',title=title,poster=poster,overview=overview,vote_average=vote_average,
        vote_count=vote_count,release_date=release_date,runtime=runtime,status=status,genres=genres,
        movie_cards=movie_cards,reviews=movie_reviews,casts=casts,cast_details=cast_details,not_in_db=not_in_db)

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port=5000)
