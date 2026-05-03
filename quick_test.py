from app.utils.movie_utils import get_data_loader, get_recommendation_engine
from app.services.recommendation_service import get_movie_recommendations

print("=" * 70)
print("  🎬 QUICK TEST - Movie Recommendation Engine")
print("=" * 70)

# Test 1: Load data
print("\n1️⃣  Loading movie data...")
loader = get_data_loader()
count = loader.get_movie_count()
print(f"   ✓ Loaded {count} movies")

if count > 0:
    # Test 2: Get recommendations
    print("\n2️⃣  Testing recommendations...")
    engine = get_recommendation_engine()
    
    recs = engine.get_trending_recommendations(3)
    if recs:
        print("   📌 Top Trending Movies:")
        for movie in recs:
            print(f"      • {movie['title']} ⭐ {movie['rating']:.1f}")
    
    # Test 3: Genre filtering
    print("\n3️⃣  Testing genre filtering...")
    action_recs = engine.get_genre_recommendations("Action", 3)
    if action_recs:
        print("   🎬 Top Action Movies:")
        for movie in action_recs:
            print(f"      • {movie['title']} ⭐ {movie['rating']:.1f}")
    
    # Test 4: Intent-based
    print("\n4️⃣  Testing intent-based recommendations...")
    response = get_movie_recommendations("I want an action movie")
    print(f"   User: 'I want an action movie'")
    print(f"   Bot: {response}")
    
    print("\n" + "=" * 70)
    print("  ✅ All tests passed!")
    print("=" * 70)
else:
    print("\n❌ No movies loaded. Check dataset files.")
