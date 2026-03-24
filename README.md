<div align="center">

# 🍿 CineMatch 🎬
**Intelligent Movie Recommendation Engine powered by Machine Learning & Sentiment Analysis.**

[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Microframework-black.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![TMDb API](https://img.shields.io/badge/Data-TMDb%20API-01B4E4.svg)](https://www.themoviedb.org/)

<br>

## 📸 Demo
![CineMatch Demo](static/demo.gif)

<br>

*A mobile-ready web application that curates precise movie suggestions using a custom hybrid scoring algorithm, while dynamically analyzing the sentiment of real-time viewer reviews via Natural Language Processing (NLP).*

</div>

---

## 📖 Overview
**CineMatch** eliminates the paradox of choice for movie nights. By simply searching for a movie you love, our hybrid Machine Learning engine instantly generates 10 highly accurate recommendations. Engineered for a premium user experience, the system seamlessly pulls dynamic metadata (posters, runtime, genres, cast profiles) and real-time audience reviews from the TMDb API. These reviews are then fed through a trained N-Gram text classifier to immediately gauge public sentiment (*Good* or *Bad*).

<br>

## ✨ Core Features

- 🧠 **Hybrid Scoring Engine:** Recommendations rely on a specialized algorithm evaluating both **Content Similarity (75%)** and **Global Popularity (25%)**. This ensures suggestions are strictly relevant while preventing obscure or excessively low-rated movies from surfacing.
- 🎭 **Real-Time Sentiment Analysis:** Fetches dynamic live reviews via the TMDb API and runs them through a trained `Multinomial Naive Bayes` classifier to instantly indicate audience verdict.
- 📱 **Interactive UI:** Features responsive CSS components (`style.css`), horizontal scrollable carousels, and intuitive tooltips optimized for both desktop pointers and mobile touch screens.
- ⚡ **Asynchronous Data Loading:** Completely AJAX-driven `/recommend` workflow. The DOM updates dynamically underneath a native loading indicator without jarring page reloads.
- 🗜️ **Memory Optimized:** Utilizes a highly compressed sparse-vector matrix (`vectors.npz`) processed on-the-fly via `scipy.sparse`, allowing the engine to generate recommendations with an extremely low memory footprint.

<br>

## 🛠️ Technology Stack

**Machine Learning & Data Processing:**
*   **pandas & numpy:** Data manipulation and complex matrix alignments.
*   **scikit-learn:** `TfidfVectorizer` for linguistic feature extraction, `MultinomialNB` for NLP sentiment training, and `cosine_similarity` for nearest-neighbor content matching.
*   **scipy:** Sparse matrix compression for the recommendation engine (`.npz`).

**Backend Server:**
*   **Flask:** Python micro-framework handling API routing and templates rendering.
*   **Requests:** Standard API consumption for dynamically fetching metadata and reviews.

**Frontend Interface:**
*   **HTML5, CSS3, & Vanilla JavaScript:** Building responsive DOM operations and AJAX state management.
*   **Jinja2:** Server-side templating engine for injecting Python variables directly into UI cards.

<br>

## ⚙️ Architecture & Data Flow

1. **User Input:** User searches via a smart dropdown powered by a local `autocomplete.js` script. The suggestion dictionary is dynamically injected into the frontend by Flask, extracted straight from the top 25,000 TMDb movie dataset DataFrame.
2. **Recommendation Engine:** Flask intercepts the payload and reads the compressed `.npz` feature vectors. Using on-the-fly math, it isolates the top highest-matching metadata profiles prioritized by language flags.
3. **Data Enrichment:** The matched IDs are cross-referenced with the `TMDb API` for HD poster paths, runtimes, genres, and cast details.
4. **Sentiment Processing:** TMDb reviews are piped into a serialized `nlp_model.pkl` classifier. The text is vectorized to output a binary `Good` or `Bad` audience rating.
5. **DOM Render:** Data dictionaries are pushed via Jinja2 into `recommend.html`, constructing dynamic movie cards and carousels directly on the client side.

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
