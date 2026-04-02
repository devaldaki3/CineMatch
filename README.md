<div align="center">

# 🍿 CineMatch 🎬
**Intelligent Movie Recommendation Engine powered by Machine Learning & Sentiment Analysis.**

[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Microframework-black.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![TMDb API](https://img.shields.io/badge/Data-TMDb%20API-01B4E4.svg)](https://www.themoviedb.org/)


*A mobile-ready web application that curates precise movie suggestions using a custom hybrid scoring algorithm, while dynamically analyzing the sentiment of real-time viewer reviews via Natural Language Processing (NLP).*

</div>

---
## 📸 Demo
![CineMatch Demo](static/demo.gif)

--- 

## 📖 Overview
**CineMatch** eliminates the paradox of choice for movie nights. By simply searching for a movie you love, our hybrid Machine Learning engine instantly generates 10 highly accurate recommendations. Engineered for a premium user experience, the system seamlessly pulls dynamic metadata (posters, runtime, genres, cast profiles) and real-time audience reviews from the TMDb API. These reviews are then fed through a trained N-Gram text classifier to immediately gauge public sentiment (*Good* or *Bad*).

<br>

## ✨ Core Features

- 🧠 **Hybrid Scoring Engine:** Recommendations rely on a specialized algorithm evaluating both **Content Similarity (75%)** and **Global Popularity (25%)**. This ensures suggestions are strictly relevant while preventing obscure or excessively low-rated movies from surfacing.
- 🎭 **Real-Time Sentiment Analysis:** Fetches dynamic live reviews via the TMDb API and runs them through a trained `Multinomial Naive Bayes` classifier to instantly indicate audience verdict.
- 📱 **Interactive UI:** Features responsive CSS components (`style.css`), horizontal scrollable carousels, and intuitive tooltips optimized for both desktop pointers and mobile touch screens.
- 🚀 **Parallel API Processing:** Engineered with Python's `concurrent.futures`, the backend fires up to 16 concurrent threads to simultaneously fetch metadata, reviews, and cast profiles from TMDb, slashing page load times by over 300%.
- ⚡ **In-Memory Caching:** Implements dual-layer caching (`@lru_cache` and dictionary-based HTML caching) ensuring that repeat movie searches load instantly in under `100ms` with zero API overhead.
- 🗜️ **Ultra-Fast Vector Math:** Replaced standard `cosine_similarity` with a pre-normalized sparse matrix dot product during startup. Computes 25,000 document vectors in just `0.5 milliseconds`, generating recommendations instantly while keeping the memory footprint incredibly low.

<br>

## 🛠️ Technology Stack

**Machine Learning & Data Processing:**
*   **pandas & numpy:** Data manipulation and complex matrix alignments.
*   **scikit-learn:** `TfidfVectorizer` for linguistic feature extraction and `MultinomialNB` for NLP sentiment training.
*   **scipy:** Sparse matrix compression (`.npz`) and lightning-fast pre-normalized vector dot products.

**Backend Server:**
*   **Flask:** Python micro-framework handling API routing and templates rendering.
*   **concurrent.futures:** 16-Worker ThreadPoolExecutor for executing parallel, non-blocking asynchronous TMDb API requests.
*   **Requests:** Backend API consumption for dynamically fetching JSON metadata and reviews.

**Frontend Interface:**
*   **HTML5, CSS3, & Vanilla JavaScript:** Building responsive DOM operations and AJAX state management.
*   **Jinja2:** Server-side templating engine for injecting Python variables directly into UI cards.

<br>

## ⚙️ Architecture & Data Flow

1. **User Input:** User searches via a smart dropdown powered by a local `autocomplete.js` script. The suggestion dictionary is dynamically injected into the frontend by Flask, extracted straight from the top 25,000 TMDb movie dataset DataFrame.
2. **Instant Caching:** The `/get_details` route first checks its internal RAM cache. If a match exists, it serves the entire pre-rendered HTML page instantly.
3. **Recommendation Engine:** Flask intercepts the payload and performs an ultra-fast matrix dot-product on our pre-normalized `.npz` feature vectors. Using on-the-fly thresholding prioritized by language flags, it isolates the top 10 highest-matching profiles in less than 1 millisecond.
4. **Parallel Data Fetch:** The `/get_details` endpoint dispatches a ThreadPoolExecutor. Instead of blocking, it makes 15+ concurrent requests to the `TMDb API` to instantly download HD poster paths, runtimes, genres, and cast details all at the exact same time.
5. **Sentiment Processing:** TMDb reviews are piped into a serialized `nlp_model.pkl` classifier. The text is vectorized to output a binary `Good` or `Bad` audience rating.
6. **DOM Render:** Data dictionaries are pushed via Jinja2 into `recommend.html`, constructing dynamic movie cards and carousels, which are then passed back to securely overwrite the client's screen.

<br>

## 🚀 Quickstart Installation (Local)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/devaldaki3/CineMatch.git
   cd CineMatch
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate       # macOS/Linux
   .\venv\Scripts\activate        # Windows
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Flask application:**
   ```bash
   python app.py
   ```

5. **Start exploring:**
   Open `http://127.0.0.1:5000/` in your browser.

<br>

## 📂 Project Structure

```text
CineMatch/
├── app.py                     # Main Flask Application routing & ML inference
├── README.md                  # Project Documentation
├── requirements.txt           # Listed dependencies for Web App and Jupyter
├── .gitignore                 # Custom Exclusion Policies
├── NoteBook_Experiments/      # Data Analysis, EDA, & Model Training notebooks 
├── data/                      # Raw datasets (TMDb 25k & Reviews)
├── models/                    # Serialized Machine Learning artifacts
│   ├── nlp_model.pkl          # Naive Bayes Sentiment Classifier
│   ├── tranform.pkl           # TfidfVectorizer rules for NLP
│   ├── vectors.npz            # Compressed Document Vectors matrix (SciPy Sparse)
│   └── movie_dict.pkl         # Lightweight Pandas Title/ID lookup dictionary
├── static/                    # Frontend Assets
│   ├── autocomplete.js        # Search bar suggestion handling
│   ├── recommend.js           # Core AJAX payloads and DOM manipulation
│   ├── style.css              # Custom responsive styling classes
│   └── image.jpg              # Default fallback/background assets
└── templates/                 # Renderable Jinja2 Views
    ├── home.html              # Search and discovery landing page
    ├── recommend.html         # Generated movie details panel
    └── genre.html             # Categorical exploration views
```

<br>

---
<div align="center">
<b>Developed with ❤️ for Movie Lovers.</b>
<br>
<i>Note: This product uses the TMDb API but is not endorsed or certified by TMDb.</i>
</div>
