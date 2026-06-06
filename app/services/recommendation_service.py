import re

from app.utils.movie_utils import get_recommendation_engine


TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w342"


def text_response(text: str) -> dict:
    return {"response": text, "movies": []}


def recommend(domain, msg):
    """
    Provide recommendations based on domain and user message.

    Args:
        domain: "movie" or "learning"
        msg: user's message/query

    Returns:
        Recommendation response dictionary
    """
    if domain == "movie":
        return get_movie_recommendations(msg)
    elif domain == "learning":
        return get_learning_recommendations(msg)
    else:
        return text_response("I can help with movie or learning recommendations. What would you like?")


def get_movie_recommendations(msg: str) -> dict:
    """Get movie recommendations based on user message."""
    try:
        engine = get_recommendation_engine()

        genre_keywords = {
            "action": ["action", "fight", "war", "battle", "spy", "thriller"],
            "comedy": ["comedy", "funny", "laugh", "humor", "hilarious"],
            "drama": ["drama", "emotional", "serious", "intense", "touching"],
            "horror": ["horror", "scary", "frighten", "terror", "creepy"],
            "romance": ["romance", "love", "romantic", "couple", "relationship"],
            "adventure": ["adventure", "explore", "journey", "expedition", "quest"],
            "sci-fi": ["sci-fi", "science fiction", "future", "space", "alien", "futuristic"],
            "animation": ["animation", "animated", "cartoon", "anime"],
            "fantasy": ["fantasy", "magic", "magical", "wizard", "mythical"],
            "thriller": ["thriller", "suspense", "mystery", "detective"],
        }

        msg_lower = msg.lower()
        detected_genre = None
        duration_match = re.search(
            r"\b(\d{2,3})\s*(?:min|mins|minute|minutes)\b",
            msg_lower,
        )

        for genre, keywords in genre_keywords.items():
            if any(keyword in msg_lower for keyword in keywords):
                detected_genre = genre
                break

        recommendations = []

        if duration_match:
            target_minutes = int(duration_match.group(1))
            recommendations = engine.get_runtime_recommendations(
                target_minutes,
                n_recommendations=5,
            )
        elif "relaxing" in msg_lower or "feel good" in msg_lower or "light" in msg_lower:
            recommendations = engine.get_genre_recommendations(
                "comedy",
                n_recommendations=5,
            )
        elif detected_genre:
            recommendations = engine.get_genre_recommendations(
                detected_genre,
                n_recommendations=5,
            )
        elif "trending" in msg_lower or "popular" in msg_lower:
            recommendations = engine.get_trending_recommendations(n_recommendations=5)
        elif "top" in msg_lower or "best" in msg_lower or "highest" in msg_lower:
            recommendations = engine.get_top_rated_recommendations(n_recommendations=5)
        else:
            recommendations = engine.get_trending_recommendations(n_recommendations=5)

        if recommendations:
            return {
                "response": "I recommend these movies:",
                "movies": [format_movie_card(movie) for movie in recommendations],
            }

        return text_response("Sorry, I couldn't find movie recommendations. Try asking about a specific genre!")

    except Exception as e:
        print(f"Error in get_movie_recommendations: {e}")
        return text_response("I had trouble fetching recommendations. Please try again!")


def format_movie_summary(movie: dict) -> str:
    """Format one movie for compact pipe-delimited UI rendering."""
    runtime = f" - {movie['runtime']}" if movie.get("runtime") else ""
    return f"{movie['title']} - {movie['rating']:.1f}/10{runtime}"


def format_movie_card(movie: dict) -> dict:
    """Format one movie for structured API/UI rendering."""
    poster_path = str(movie.get("poster_path", "") or "").strip()
    if poster_path.lower() in {"", "nan", "none"}:
        poster_path = ""
    if poster_path and not poster_path.startswith("/"):
        poster_path = f"/{poster_path}"
    poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else ""
    return {
        "title": movie.get("title", "Unknown"),
        "rating": movie.get("rating", 0),
        "runtime": movie.get("runtime", ""),
        "release_year": movie.get("release_year", ""),
        "genres": movie.get("genres", ""),
        "overview": movie.get("overview", ""),
        "poster_path": poster_path,
        "poster_url": poster_url,
    }


def get_learning_recommendations(msg: str) -> dict:
    """Get learning resource recommendations."""
    recommendations = {
        "programming": [
            "freeCodeCamp - Free coding courses",
            "Codecademy - Interactive coding lessons",
            "LeetCode - Programming problem practice",
        ],
        "data science": [
            "Fast.ai - Practical deep learning",
            "Coursera - Data science specializations",
            "Kaggle - Real-world data projects",
        ],
        "web development": [
            "MDN Web Docs - Web standards documentation",
            "The Odin Project - Full stack curriculum",
            "Frontend Masters - Advanced web skills",
        ],
        "general": [
            "Coursera - University-level courses",
            "edX - Quality online education",
            "YouTube Learning - Video tutorials",
            "Khan Academy - Free educational content",
        ],
    }

    msg_lower = msg.lower()

    for topic in recommendations.keys():
        if topic in msg_lower:
            return text_response("You might like: " + ", ".join(recommendations[topic][:2]))

    return text_response("You might like: " + ", ".join(recommendations["general"][:3]))
