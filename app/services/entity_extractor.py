import re

GENRES = [
    "action", "comedy", "drama", "horror",
    "romance", "adventure", "sci-fi",
    "animation", "fantasy", "thriller"
]

def extract_entities(text: str):
    text = text.lower()
    entities = {}

    # Genre detection
    for genre in GENRES:
        if genre in text:
            entities["genre"] = genre
            break

    # Year detection
    year_match = re.search(r"(19|20)\d{2}", text)
    if year_match:
        entities["year"] = year_match.group()

    # Keywords fallback
    entities["keywords"] = text.split()

    return entities