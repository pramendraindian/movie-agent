# Quick Start Guide - TMDB Movie Recommendation Engine

## Installation & Setup

### Step 1: Ensure Dependencies are Installed
```bash
pip install pandas numpy scikit-learn
```

### Step 2: Verify Dataset
```bash
# Check dataset exists
ls -la dataset/TMDB_movie_dataset_v11.csv
```

### Step 3: Test the Engine
```bash
python quick_test.py
```

---

## Basic Usage

### Load Movie Data
```python
from app.utils.movie_utils import get_data_loader, get_recommendation_engine

# Initialize data loader
loader = get_data_loader()
movie_count = loader.get_movie_count()
print(f"✓ Loaded {movie_count} movies")

# Get all movies as DataFrame
all_movies = loader.get_all_movies()
```

### Get Recommendations Engine
```python
# Create recommendation engine
engine = get_recommendation_engine()
```

---

## Common Tasks

### 1. Get Trending Movies
```python
trending = engine.get_trending_recommendations(n_recommendations=5)

for movie in trending:
    print(f"🎬 {movie['title']}")
    print(f"   ⭐ Rating: {movie['rating']}/10")
    print(f"   📊 Popularity: {movie['popularity']}")
    print(f"   📅 Release: {movie['release_year']}")
```

**Output:**
```
🎬 Elemental
   ⭐ Rating: 7.8/10
   📊 Popularity: 1008.9
   📅 Release: 2023
```

### 2. Find Movies by Genre
```python
# Supported genres: Action, Comedy, Drama, Horror, Romance, Sci-Fi, Animation, etc.
action_movies = engine.get_genre_recommendations("Action", n_recommendations=5)

for movie in action_movies:
    print(f"{movie['title']} - {movie['genres']}")
```

### 3. Get Top-Rated Movies
```python
best_movies = engine.get_top_rated_recommendations(
    n_recommendations=5,
    min_votes=100  # Only movies with 100+ votes
)

for movie in best_movies:
    print(f"{movie['title']} ⭐ {movie['rating']} ({movie['vote_count']} votes)")
```

### 4. Search for Movies
```python
# Search by title
results = engine.search_movies("Matrix", n_recommendations=5)

for movie in results:
    print(f"Found: {movie['title']}")
```

### 5. Find Similar Movies
```python
# Get movies similar to a specific movie
similar = engine.get_content_based_recommendations(
    movie_title="The Dark Knight",
    n_recommendations=5
)

for movie in similar:
    print(f"Similar: {movie['title']}")
```

### 6. Intent-Based Recommendations (Natural Language)
```python
from app.services.recommendation_service import get_movie_recommendations

# Simple natural language processing
queries = [
    "I want an action movie",
    "Show me trending movies",
    "What are the best movies?",
    "Recommend a comedy",
    "Suggest something romantic",
    "Any horror recommendations?"
]

for query in queries:
    result = get_movie_recommendations(query)
    print(f"User: {query}")
    print(f"Bot: {result}\n")
```

---

## Movie Data Fields

Each movie recommendation includes:

```python
movie = {
    'id': 123,                          # TMDB Movie ID
    'title': 'The Dark Knight',         # Movie title
    'rating': 8.5,                      # Rating (0-10)
    'genres': 'Action, Crime, Drama',   # Genre list
    'overview': 'When the menace...',   # Description
    'popularity': 200.5,                # Popularity score
    'vote_count': 15000,                # Number of votes
    'keywords': 'Batman, Joker',        # Keywords
    'release_date': '2008-07-18',       # Full date
    'release_year': '2008',             # Year only
    'runtime': '152 min',               # Duration
    'poster_path': '/path/to/poster.jpg',     # Poster image
    'backdrop_path': '/path/to/backdrop.jpg', # Backdrop image
    'tagline': 'Darkness falls...',    # Movie tagline
}
```

---

## Advanced Filtering

### Filter by Multiple Criteria
```python
from app.utils.movie_utils import get_data_loader

loader = get_data_loader()
df = loader.get_all_movies()

# Get action movies from 2020-2023 with high ratings
filtered = df[
    (df['genres'].str.contains('Action', case=False, na=False)) &
    (df['release_year'].astype(int) >= 2020) &
    (df['rating'] >= 7.0)
]

print(f"Found {len(filtered)} movies matching criteria")
for idx, movie in filtered.iterrows():
    print(f"- {movie['title']} ({movie['release_year']})")
```

### Get Movies by Release Year Range
```python
recent_classics = df[
    (df['rating'] >= 8.0) &
    (df['release_year'].astype(int) >= 2015) &
    (df['release_year'].astype(int) <= 2022)
]
```

---

## Performance Tips

### 1. Cache Data Locally
```python
# First call loads data
engine = get_recommendation_engine()  # Takes ~5-10 seconds

# Subsequent calls use cached data
trending = engine.get_trending_recommendations()  # <100ms
```

### 2. Batch Recommendations
```python
# Instead of multiple single queries
queries = ['Action', 'Comedy', 'Drama']

# Get all at once
recommendations = {
    genre: engine.get_genre_recommendations(genre, 5)
    for genre in queries
}
```

### 3. Limit Result Size
```python
# Use n_recommendations parameter to reduce processing
recs = engine.get_trending_recommendations(n_recommendations=3)
```

---

## Troubleshooting

### No Movies Loaded
```python
loader = get_data_loader()
if loader.get_movie_count() == 0:
    print("❌ Dataset not found!")
    # Check file exists: dataset/TMDB_movie_dataset_v11.csv
```

### Unicode Encoding Error on Windows
```bash
# Set console encoding before running
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python test_recommendations.py
```

### Memory Issues with Large Dataset
```python
# Reduce loaded movies in movie_utils.py
# Change nrows parameter in _load_data():
# nrows=5000  # Change to smaller number like 2000
```

---

## Integration with Flask/FastAPI

### Flask Example
```python
from flask import Flask, jsonify
from app.utils.movie_utils import get_recommendation_engine

app = Flask(__name__)
engine = get_recommendation_engine()

@app.route('/api/trending')
def trending():
    recs = engine.get_trending_recommendations(5)
    return jsonify(recs)

@app.route('/api/genre/<genre>')
def genre_recs(genre):
    recs = engine.get_genre_recommendations(genre, 5)
    return jsonify(recs)
```

### FastAPI Example
```python
from fastapi import FastAPI
from app.utils.movie_utils import get_recommendation_engine

app = FastAPI()
engine = get_recommendation_engine()

@app.get("/api/trending")
def get_trending():
    return engine.get_trending_recommendations(5)

@app.get("/api/genre/{genre}")
def get_by_genre(genre: str):
    return engine.get_genre_recommendations(genre, 5)
```

---

## Examples Output

### Trending Query
```
Input: engine.get_trending_recommendations(3)

Output:
[
  {
    'id': 507089,
    'title': 'Elemental',
    'rating': 7.8,
    'genres': 'Animation, Comedy, Family, Fantasy, Romance',
    'overview': 'In a city where fire, water, land and air...',
    'popularity': 1008.9,
    'vote_count': 2850,
    'keywords': 'opposites attract, element',
    'release_date': '2023-06-14',
    'release_year': '2023',
    'runtime': '96 min',
    'poster_path': '/...',
    'backdrop_path': '/...',
    'tagline': 'The opposites attract.'
  },
  ...
]
```

### Genre Query
```
Input: engine.get_genre_recommendations('Horror', 3)

Output:
[
  {
    'id': 278,
    'title': 'The Shining',
    'rating': 8.2,
    'genres': 'Drama, Horror',
    'overview': 'Jack Torrance, a guy trying to get his act together...',
    'popularity': 92.5,
    'vote_count': 8847,
    'keywords': 'haunted hotel, madness, psychological horror',
    'release_date': '1980-05-23',
    'release_year': '1980',
    'runtime': '146 min',
    ...
  },
  ...
]
```

---

## Dataset Statistics

```
Total Movies:        1,500
Genres Included:     20+
Rating Range:        0.0 - 10.0
Year Range:          1912 - 2023
Languages:           100+
Avg Rating:          7.2
Avg Runtime:         108 min
```

---

## Common Queries & Solutions

| Need | Solution |
|------|----------|
| Find action movies | `engine.get_genre_recommendations('Action')` |
| Get best movies | `engine.get_top_rated_recommendations()` |
| Find trending | `engine.get_trending_recommendations()` |
| Similar to movie X | `engine.get_content_based_recommendations('X')` |
| Search by keyword | `engine.search_movies('keyword')` |
| Natural language | `get_movie_recommendations('I want...')` |

---

## References

- **TMDB Dataset**: TMDB_movie_dataset_v11.csv
- **Location**: `dataset/TMDB_movie_dataset_v11.csv`
- **Size**: ~50MB (1500+ movies after processing)
- **Format**: CSV with 24 columns

---

**Last Updated**: 2026-05-02 | **Status**: Production Ready ✅
