# 🎬 Movie Recommendation Engine - Documentation

## Overview

This recommendation engine provides intelligent movie suggestions using multiple algorithms and data analysis techniques. It leverages your TMDB movie dataset to deliver personalized recommendations based on user preferences.

## Features

### 1. **Content-Based Filtering**
Recommends movies similar to ones the user likes based on:
- Movie genres
- Keywords and descriptions
- Text similarity (TF-IDF vectorization)
- Cosine similarity metrics

```python
engine.get_content_based_recommendations("Inception", n_recommendations=5)
```

### 2. **Genre-Based Filtering**
Recommends the best movies in a specific genre, sorted by:
- User rating
- Popularity metrics

```python
engine.get_genre_recommendations("Action", n_recommendations=5)
```

### 3. **Trending Recommendations**
Shows currently popular and highly-rated movies:
- Combines popularity metrics with ratings
- Great for discovering new content

```python
engine.get_trending_recommendations(n_recommendations=5)
```

### 4. **Top-Rated Filtering**
Recommends the highest-rated movies with minimum vote thresholds:
- Quality assurance through minimum vote counts
- Prevents bias toward niche films

```python
engine.get_top_rated_recommendations(n_recommendations=5, min_votes=50)
```

### 5. **Search Functionality**
Intelligent search across:
- Movie titles (exact and partial matches)
- Movie descriptions and keywords
- Returns sorted results by rating

```python
engine.search_movies("superhero", n_recommendations=5)
```

### 6. **Intent-Based Recommendations**
Automatically detects user intent from natural language:
- Genre detection (action, comedy, drama, horror, etc.)
- Quality filters (trending, top-rated, best)
- Context-aware recommendations

```python
get_movie_recommendations("I want a scary movie")
# Returns: Horror movie recommendations
```

## Architecture

### Components

```
app/
├── utils/
│   └── movie_utils.py          # Core recommendation engine
│       ├── MovieDataLoader     # Loads and preprocesses data
│       ├── RecommendationEngine # All recommendation algorithms
│       └── Singleton instances  # Global engine instances
├── services/
│   └── recommendation_service.py # Integration with chatbot intent system
└── data/
    └── intents.json            # Intent definitions
```

### Key Classes

#### `MovieDataLoader`
**Purpose**: Loads and preprocesses movie CSV data

**Methods**:
- `__init__(dataset_path)` - Initialize with dataset path
- `_load_data()` - Load CSV file
- `_preprocess_tmdb_data()` - Clean and normalize data
- `get_all_movies()` - Return all loaded movies
- `get_movie_count()` - Return total movie count

**Data Processing**:
- Removes duplicates
- Fills missing values
- Normalizes numeric fields
- Filters invalid entries

#### `RecommendationEngine`
**Purpose**: Provides movie recommendations using multiple algorithms

**Key Methods**:
- `get_content_based_recommendations()` - Similar movie recommendations
- `get_genre_recommendations()` - Genre-specific recommendations
- `get_trending_recommendations()` - Popular movies
- `get_top_rated_recommendations()` - Highest-rated movies
- `search_movies()` - Search functionality
- `_build_similarity_matrix()` - TF-IDF + Cosine similarity
- `_format_recommendations()` - Standard output format

**Output Format**:
```python
{
    'title': 'Movie Title',
    'rating': 8.5,
    'genres': 'Action, Adventure',
    'overview': 'Movie description...',
    'popularity': 45.3
}
```

## Usage Examples

### Basic Setup
```python
from app.utils.movie_utils import get_recommendation_engine

# Get or create engine (singleton pattern)
engine = get_recommendation_engine()
```

### Example 1: Find Similar Movies
```python
recs = engine.get_content_based_recommendations("Avatar", n_recommendations=5)
for movie in recs:
    print(f"{movie['title']} ⭐ {movie['rating']:.1f}")
```

### Example 2: Get Genre Recommendations
```python
# Get top 5 action movies
action_movies = engine.get_genre_recommendations("Action", n_recommendations=5)

# Sort by popularity instead of rating
popular_dramas = engine.get_genre_recommendations("Drama", n_recommendations=5, sort_by="popularity")
```

### Example 3: Search for Movies
```python
# Search for superhero movies
superhero_movies = engine.search_movies("superhero", n_recommendations=5)

# Search for romantic movies
romantic_movies = engine.search_movies("love story", n_recommendations=10)
```

### Example 4: Integration with Intent Classification
```python
from app.services.recommendation_service import get_movie_recommendations

# These work with your existing intent system
response = get_movie_recommendations("I want an exciting action movie")
response = get_movie_recommendations("Recommend a comedy please")
response = get_movie_recommendations("What are the trending movies?")
```

## Genre Keywords

The engine recognizes these genre patterns:

- **Action**: action, fight, war, battle, spy, thriller
- **Comedy**: comedy, funny, laugh, humor, hilarious
- **Drama**: drama, emotional, serious, intense, touching
- **Horror**: horror, scary, frighten, terror, creepy
- **Romance**: romance, love, romantic, couple, relationship
- **Adventure**: adventure, explore, journey, expedition, quest
- **Sci-Fi**: sci-fi, science fiction, future, space, alien
- **Animation**: animation, animated, cartoon, anime
- **Fantasy**: fantasy, magic, magical, wizard, mythical
- **Thriller**: thriller, suspense, mystery, detective

## Performance Optimization

### Singleton Pattern
The engine uses singleton instances to avoid reloading data:
```python
_data_loader = None
_recommendation_engine = None

def get_recommendation_engine():
    global _recommendation_engine
    if _recommendation_engine is None:
        # Initialize only once
        _recommendation_engine = RecommendationEngine(...)
    return _recommendation_engine
```

### Lazy Loading
Data is loaded only when first requested, improving startup time.

### Caching
Similarity matrix is computed once and cached for fast recommendations.

## Testing

Run the test suite:
```bash
python test_recommendations.py
```

**Test Coverage**:
- ✓ Data loading and preprocessing
- ✓ Content-based recommendations
- ✓ Genre-based filtering
- ✓ Trending recommendations
- ✓ Top-rated filtering
- ✓ Search functionality
- ✓ Intent-based recommendations

## Dependencies

```
pandas          # Data manipulation
scikit-learn    # TF-IDF and similarity metrics
numpy           # Numerical operations
```

## Error Handling

The engine includes comprehensive error handling:
- Invalid/missing data handling
- Genre not found gracefully returns empty list
- Movie not found returns empty recommendations
- Fallback to trending movies when no specific match

## Future Enhancements

1. **Collaborative Filtering**: Learn from user ratings
2. **Hybrid Recommendations**: Combine multiple algorithms
3. **User Preferences**: Remember past recommendations
4. **Real-time Updates**: Integrate live TMDB API
5. **Rating Prediction**: ML model to predict user ratings
6. **Language-specific**: Recommendations by language
7. **Time-based**: Movies from specific decades/years

## Troubleshooting

### No Recommendations Returned
- Check that CSV files are in the `dataset/` directory
- Verify data is properly loaded: `get_data_loader().get_movie_count()`
- Check genre spelling matches dataset

### Slow Performance
- First run builds similarity matrix (normal)
- Subsequent runs use cached matrix
- For very large datasets, consider filtering by popularity

### Missing Data
- Engine handles missing values gracefully
- Defaults to trending movies if criteria not met

---

**Created**: 2024
**Version**: 1.0
**Status**: Production Ready
