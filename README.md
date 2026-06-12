
# 🚀 Movie Recommendation Chatbot
Dataset: https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies/data
        # Command1
            python -m venv .venv
        # Command2
        README.md
            (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& C:\IITD AIML\Projects\Movie Agent\movie-agent\.venv\Scripts\Activate.ps1)
        # Command3
            python -m pip install -r requirements.txt

------------------ Moni's Models--

Demo script for presentation
# Baseline
python train.py
INTENT_MODEL_PATH=data.pth uvicorn app.main:app --port 8001

# DistilBERT multiclass
python train_bert.py
INTENT_MODEL_PATH=intent_model uvicorn app.main:app --port 8001

# ModernBERT sentence-pair (best approach)
python modern_bert_train.py
INTENT_MODEL_PATH=intent_model uvicorn app.main:app --port 8001

Note: we have to train before you start the chat for inference since models are diff. Also you can run on port 8000, for me my project was running on that so I had to use a diff one

# Same test for all
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"recommend a comedy movie"}'




----------------------------------------------





    python download_nltk.py
    python train.py
    python app/main.py
    Postman -
    Endpoint: http://127.0.0.1:8000/chat
    Try with below payloads
    Payload:
        {
            "message":"Hi"
        }
    -------------------
        Response:
        {
            "response": "Hello! Ask me for movies or learning."
        }
____________________________________
    Payload: 
    {
    "message":"adventure movie"
    }
    -----------------------------
    Response
    {
        "response": "Try: Inception, Avengers, Interstellar"
    }

## Features
- FastAPI backend
- Intent classification (PyTorch)
- LLM fallback (OpenAI)
- Movie recommendations (TMDB API)
- Modular architecture
- Ready for Docker deployment

## Run
### Windows quick start

Run setup once:

```bat
scripts\setup.bat
```

Then start the backend and Streamlit UI anytime with:

```bat
scripts\run_app.bat
```

You can also run them separately:

```bat
scripts\run_api.bat
scripts\run_ui.bat
```

### Manual commands

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_nltk.py
.\.venv\Scripts\python.exe train.py
.\.venv\Scripts\python.exe app/main.py
.\.venv\Scripts\python.exe -m streamlit run chatbot_ui.py
```

## API

POST /chat

```json
{"message": "Suggest a comedy movie"}
```
## 🏗️ Architecture Overview

This project follows a **Hybrid AI Architecture** combining:
- Intent Classification (ML)
- LLM Fallback
- External APIs (Recommendations)

<p align="center">
  <img src="diagrams/ArchDiagram.png" width="900"/>
</p>

<p align="center">
  <img src="diagrams/CineGenie.png" width="900"/>
</p>

## Contributors

- [Moni](https://github.com/emonhaz)
- [Pramendra Singh](https://github.com/your-github-username)
- [Sajith](https://github.com/sajithkn-alt)
- [Shashank](https://github.com/shashank160790)




**Apporach:1**
### **1. Training Phase** (`train_bert.py`)

```
Intent Data → Data Preparation → Model Training → Saved Model
```

**What happens:**
- **Load intents**: Reads `new_intents.json` containing intent categories (greeting, movie_action, movie_comedy, etc.) with user patterns and bot responses
- **Prepare data**: 
  - Extracts all patterns and assigns them to their intent tags
  - Creates mappings: `tag2id` (e.g., "movie_action" → 0) and `id2tag` (reverse mapping)
  - Splits data: 80% training, 20% validation
- **Tokenize**: Uses DistilBERT tokenizer to convert text patterns into token IDs
- **Train model**: 
  - DistilBertForSequenceClassification trained for 20 epochs
  - Learns to classify user input patterns into intent categories
  - Uses learning rate 2e-5, batch size 4
  - Saves best model based on validation loss
- **Save artifacts**: 
  - `intent_model/` directory with model weights and tokenizer
  - `intent_model/meta.pkl` with tag mappings and config

---

### **2. Inference/Prediction Phase** (`modern_bert_predict.py`)

```
User Input → Tokenization → Model Prediction → Intent Classification → Response
```

**What happens:**
- **Load model**: Loads pre-trained DistilBERT model and tokenizer from `intent_model/`
- **Predict intent**: 
  - Encodes user input with tokenizer
  - Runs through model to get logits
  - Converts to probabilities using softmax
  - Returns top predicted intent + confidence score
- **Threshold check**: If confidence < 0.65, returns "fallback" (I don't understand)
- **Output**: Intent name + confidence percentage

---

### **3. Chatbot UI & API Layer** (`chatbot_ui.py`)

```
User Message → Streamlit Frontend → FastAPI Backend → Intent Prediction → Response Selection → Movie Recommendations
```

**What happens:**

**Frontend (Streamlit):**
1. User types message in chat interface
2. Sends via POST request to FastAPI backend (`http://localhost:8000/chat`)
3. Displays bot response with formatted message bubbles
4. Renders movie cards with posters, ratings, year, runtime

**Backend (FastAPI - not shown but referenced):**
1. Receives user message
2. Uses `modern_bert_predict.py` to predict intent
3. Looks up response in intents JSON based on predicted intent tag
4. For movie recommendations, queries TMDB API for actual movie data
5. Returns formatted response with movie details (title, poster, rating, etc.)

---

### **4. Intent Categories & Data Flow**

Your `intents.json` has these main categories:

| Intent | Purpose | Example Response |
|--------|---------|------------------|
| **greeting** | Hello interactions | "Hello! I can recommend movies..." |
| **movie_action** | Action movies | "Try: John Wick, Mad Max..." |
| **movie_comedy** | Funny movies | "Try: The Hangover, Superbad..." |
| **movie_horror** | Scary movies | "Try: The Conjuring, IT..." |
| **movie_mood_happy** | Cheer-up content | "Try: Forrest Gump..." |
| **movie_trending** | Popular now | "Popular picks: Oppenheimer, Dune..." |
| **fallback** | Unrecognized input | "Sorry, I didn't get that..." |

---

### **5. Complete User Journey Example**

```
1. User: "I want something funny to watch"
   ↓
2. Tokenizer: Converts to token IDs
   ↓
3. Model: Predicts intent "movie_comedy" (confidence 0.92)
   ↓
4. Response lookup: Gets responses for "movie_comedy" tag
   ↓
5. Backend: Selects response + queries TMDB for comedy movies
   ↓
6. Frontend: Displays "Try: The Hangover, Superbad, The Mask" 
            + movie cards with posters and ratings
```

---

### **Key Components Summary**

| Component | Role |
|-----------|------|
| **`train_bert.py`** | Trains DistilBERT on intent patterns |
| **`modern_bert_predict.py`** | Classifies user input into intents |
| **`chatbot_ui.py`** | Streamlit interface for user interaction |
| **`intents.json`** | Intent definitions and responses |
| **FastAPI backend** | Orchestrates prediction + movie data lookup |
| **TMDB API** | Provides movie metadata (posters, ratings, etc.) |

The system is essentially a **text classification pipeline** that understands what users want (comedy, action, mood) and responds with personalized movie suggestions!
