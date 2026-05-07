from app.utils.movie_utils import get_recommendation_engine
from app.services.entity_extractor import extract_entities
import re


def recommend(domain, msg):
    """
    Provide recommendations based on domain and user message.
    
    Args:
        domain: "movie" or "learning"
        msg: user's message/query
    
    Returns:
        Recommendation response string
    """
    if domain == "movie":
        return get_movie_recommendations(msg)
    elif domain == "learning":
        return get_learning_recommendations(msg)
    else:
        return "I can help with movie or learning recommendations. What would you like?"

def get_movie_recommendations(msg: str) -> str:
    try:
        engine = get_recommendation_engine()

        # entities = extract_entities(msg)

        # if "genre" in entities:
        #     recommendations = engine.get_genre_recommendations(
        #         entities["genre"], n_recommendations=5
        #     )

        # elif "year" in entities:
        #     recommendations = engine.get_movies_by_year(
        #         entities["year"]
        #     )

        # elif "top" in msg.lower() or "best" in msg.lower():
        #     recommendations = engine.get_top_rated_recommendations(5)

        # else:
        #     recommendations = engine.get_trending_recommendations(5)
        entities = extract_entities(msg)

        if "genre" in entities:
            recommendations = engine.get_genre_recommendations(
                entities["genre"],
                n_recommendations=5
            )

        elif "year" in entities:
            recommendations = engine.get_movies_by_year(
                entities["year"]
            )

        elif entities.get("sort") == "rating":
            recommendations = engine.get_top_rated_recommendations(5)

        elif entities.get("sort") == "trending":
            recommendations = engine.get_trending_recommendations(5)

        else:
            recommendations = engine.get_trending_recommendations(5)

        if recommendations:
            return "I recommend: " + ", ".join(
                [f"{m['title']} ⭐ {m['rating']:.1f}" for m in recommendations[:3]]
            )

        return "No recommendations found."

    except Exception as e:
        return "Error fetching recommendations."

# def get_movie_recommendations(msg: str) -> str:
#     """Get movie recommendations based on user message"""
#     try:
#         engine = get_recommendation_engine()
        
#         # Extract genre or keywords from message
#         genre_keywords = {
#             'action': ['action', 'fight', 'war', 'battle', 'spy', 'thriller'],
#             'comedy': ['comedy', 'funny', 'laugh', 'humor', 'hilarious'],
#             'drama': ['drama', 'emotional', 'serious', 'intense', 'touching'],
#             'horror': ['horror', 'scary', 'frighten', 'terror', 'creepy'],
#             'romance': ['romance', 'love', 'romantic', 'couple', 'relationship'],
#             'adventure': ['adventure', 'explore', 'journey', 'expedition', 'quest'],
#             'sci-fi': ['sci-fi', 'science fiction', 'future', 'space', 'alien', 'futuristic'],
#             'animation': ['animation', 'animated', 'cartoon', 'anime'],
#             'fantasy': ['fantasy', 'magic', 'magical', 'wizard', 'mythical'],
#             'thriller': ['thriller', 'suspense', 'mystery', 'detective']
#         }
        
#         msg_lower = msg.lower()
#         detected_genre = None
        
#         # Detect genre from keywords
#         for genre, keywords in genre_keywords.items():
#             if any(keyword in msg_lower for keyword in keywords):
#                 detected_genre = genre
#                 break
        
#         # Get recommendations
#         recommendations = []
        
#         if detected_genre:
#             recommendations = engine.get_genre_recommendations(detected_genre, n_recommendations=5)
#         elif 'trending' in msg_lower or 'popular' in msg_lower:
#             recommendations = engine.get_trending_recommendations(n_recommendations=5)
#         elif 'top' in msg_lower or 'best' in msg_lower or 'highest' in msg_lower:
#             recommendations = engine.get_top_rated_recommendations(n_recommendations=5)
#         else:
#             # If no specific criteria, return trending movies
#             recommendations = engine.get_trending_recommendations(n_recommendations=5)
        
#         # Format response
#         if recommendations:
#             movie_titles = [movie['title'] for movie in recommendations[:3]]
#             rating_info = " | ".join([
#                 f"{movie['title']} ⭐ {movie['rating']:.1f}" 
#                 for movie in recommendations[:3]
#             ])
#             return f"I recommend: {rating_info}"
#         else:
#             return "Sorry, I couldn't find movie recommendations. Try asking about a specific genre!"
    
#     except Exception as e:
#         print(f"Error in get_movie_recommendations: {e}")
#         return "I had trouble fetching recommendations. Please try again!"


def get_learning_recommendations(msg: str) -> str:
    """Get learning resource recommendations"""
    recommendations = {
        'programming': [
            'freeCodeCamp - Free coding courses',
            'Codecademy - Interactive coding lessons',
            'LeetCode - Programming problem practice'
        ],
        'data science': [
            'Fast.ai - Practical deep learning',
            'Coursera - Data science specializations',
            'Kaggle - Real-world data projects'
        ],
        'web development': [
            'MDN Web Docs - Web standards documentation',
            'The Odin Project - Full stack curriculum',
            'Frontend Masters - Advanced web skills'
        ],
        'general': [
            'Coursera - University-level courses',
            'edX - Quality online education',
            'YouTube Learning - Video tutorials',
            'Khan Academy - Free educational content'
        ]
    }
    
    msg_lower = msg.lower()
    
    # Detect learning topic
    for topic in recommendations.keys():
        if topic in msg_lower:
            return "You might like: " + ", ".join(recommendations[topic][:2])
    
    # Return general recommendations
    return "You might like: " + ", ".join(recommendations['general'][:3])
