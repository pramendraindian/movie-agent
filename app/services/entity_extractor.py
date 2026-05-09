# import re

# GENRES = [
#     "action", "comedy", "drama", "horror",
#     "romance", "adventure", "sci-fi",
#     "animation", "fantasy", "thriller"
# ]

# def extract_entities(text: str):
#     text = text.lower()
#     entities = {}

#     # Genre detection
#     for genre in GENRES:
#         if genre in text:
#             entities["genre"] = genre
#             break

#     # Year detection
#     year_match = re.search(r"(19|20)\d{2}", text)
#     if year_match:
#         entities["year"] = year_match.group()

#     # Keywords fallback
#     entities["keywords"] = text.split()

#     return entities


import re


GENRES = {
    "action": ["action", "fight", "battle", "war", "spy"],
    "comedy": ["comedy", "funny", "humor", "laugh"],
    "drama": ["drama", "emotional", "serious"],
    "horror": ["horror", "scary", "creepy", "terror"],
    "romance": ["romance", "love", "romantic"],
    "adventure": ["adventure", "journey", "quest"],
    "sci-fi": ["sci-fi", "science fiction", "space", "alien", "future"],
    "animation": ["animation", "animated", "cartoon", "anime"],
    "fantasy": ["fantasy", "magic", "wizard"],
    "thriller": ["thriller", "suspense", "mystery"]
}


MOODS = {
    "feel_good": ["feel good", "uplifting", "happy"],
    "dark": ["dark", "intense", "serious"],
    "mind_bending": ["mind bending", "psychological", "twist"],
    "family": ["family", "kids", "children"]
}


def extract_entities(text: str):

    text = text.lower()

    entities = {}

    # -----------------------
    # Genre detection
    # -----------------------
    for genre, keywords in GENRES.items():

        if any(keyword in text for keyword in keywords):
            entities["genre"] = genre
            break

    # -----------------------
    # Mood detection
    # -----------------------
    for mood, keywords in MOODS.items():

        #if any(keyword in text for keyword in keywords):
        if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
            entities["mood"] = mood
            break

    # -----------------------
    # Year detection
    # -----------------------
    year_match = re.search(r"(19|20)\d{2}", text)

    if year_match:
        entities["year"] = int(year_match.group())

    # -----------------------
    # Rating intent
    # -----------------------
    if any(word in text for word in ["top", "best", "highest rated"]):
        entities["sort"] = "rating"

    # -----------------------
    # Trending intent
    # -----------------------
    if any(word in text for word in ["trending", "popular", "latest"]):
        entities["sort"] = "trending"

    return entities