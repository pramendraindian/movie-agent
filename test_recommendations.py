#!/usr/bin/env python
"""
Demo script to test the movie recommendation engine
"""

from app.utils.movie_utils import get_data_loader, get_recommendation_engine
from app.services.recommendation_service import get_movie_recommendations
import json


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_recommendations(movies, title="Recommendations"):
    """Pretty print movie recommendations"""
    print(f"\n{title}:")
    print("-" * 70)
    for i, movie in enumerate(movies, 1):
        print(f"\n{i}. {movie['title']}")
        print(f"   ⭐ Rating: {movie['rating']:.1f}/10")
        print(f"   📽️  Genres: {movie['genres']}")
        print(f"   📊 Popularity: {movie['popularity']:.1f}")
        if movie['overview']:
            overview = movie['overview'][:120] + "..." if len(movie['overview']) > 120 else movie['overview']
            print(f"   📝 {overview}")


def test_data_loader():
    """Test data loading"""
    print_section("TESTING DATA LOADER")
    
    loader = get_data_loader()
    count = loader.get_movie_count()
    print(f"✓ Successfully loaded {count} movies!")
    
    df = loader.get_all_movies()
    if count > 0:
        print(f"\nDataset columns: {list(df.columns)[:10]}...")
        print(f"Sample movie: {df.iloc[0]['title']}")


def test_content_based_recommendations():
    """Test content-based recommendations"""
    print_section("TESTING CONTENT-BASED RECOMMENDATIONS")
    
    engine = get_recommendation_engine()
    
    # Try different popular movie titles
    test_titles = ["Inception", "Avatar", "Interstellar"]
    
    for title in test_titles:
        recs = engine.get_content_based_recommendations(title, n_recommendations=3)
        if recs:
            print(f"\n📌 Movies similar to '{title}':")
            print_recommendations(recs)
            break
    else:
        print("⚠️ Could not find similar movies in database")


def test_genre_recommendations():
    """Test genre-based recommendations"""
    print_section("TESTING GENRE-BASED RECOMMENDATIONS")
    
    engine = get_recommendation_engine()
    
    genres = ["Action", "Comedy", "Drama", "Horror", "Romance"]
    
    for genre in genres:
        recs = engine.get_genre_recommendations(genre, n_recommendations=3)
        if recs:
            print(f"\n🎬 Top {genre} movies:")
            for movie in recs[:3]:
                print(f"  • {movie['title']} ⭐ {movie['rating']:.1f}")
            break


def test_trending_recommendations():
    """Test trending recommendations"""
    print_section("TESTING TRENDING RECOMMENDATIONS")
    
    engine = get_recommendation_engine()
    recs = engine.get_trending_recommendations(n_recommendations=5)
    
    if recs:
        print_recommendations(recs, "🔥 Trending Movies")
    else:
        print("⚠️ Could not fetch trending movies")


def test_top_rated_recommendations():
    """Test top-rated recommendations"""
    print_section("TESTING TOP-RATED RECOMMENDATIONS")
    
    engine = get_recommendation_engine()
    recs = engine.get_top_rated_recommendations(n_recommendations=5, min_votes=50)
    
    if recs:
        print_recommendations(recs, "🏆 Top Rated Movies")
    else:
        print("⚠️ Could not fetch top-rated movies")


def test_search():
    """Test movie search"""
    print_section("TESTING MOVIE SEARCH")
    
    engine = get_recommendation_engine()
    
    queries = ["love", "adventure", "superhero"]
    
    for query in queries:
        recs = engine.search_movies(query, n_recommendations=3)
        if recs:
            print(f"\n🔍 Search results for '{query}':")
            for movie in recs[:2]:
                print(f"  • {movie['title']}")
            break


def test_intent_based_recommendations():
    """Test intent-based recommendations"""
    print_section("TESTING INTENT-BASED RECOMMENDATIONS")
    
    test_queries = [
        "I want an action movie",
        "recommend me a comedy",
        "show me trending movies",
        "what are the best movies",
        "suggest something romantic",
        "any horror recommendations"
    ]
    
    for query in test_queries:
        response = get_movie_recommendations(query)
        print(f"\n👤 User: {query}")
        print(f"🤖 Bot: {response}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  🎬 MOVIE RECOMMENDATION ENGINE - DEMO & TESTING")
    print("="*70)
    
    try:
        # Run tests
        test_data_loader()
        test_genre_recommendations()
        test_trending_recommendations()
        test_top_rated_recommendations()
        test_search()
        test_intent_based_recommendations()
        
        print_section("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
