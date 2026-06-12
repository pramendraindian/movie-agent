
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

## Local-First RAG (Feature Flagged)

RAG is off by default and does not change current behavior until enabled.

### 1) Install / update deps

```bat
scripts\setup.bat
```

### 2) Build local vector index

```bat
scripts\build_rag_index.bat
```

### 3) Start Ollama and pull a local model

```bat
ollama pull phi3:mini
```

### 4) Enable fallback-only RAG

```bat
set RAG_ENABLED=true
set RAG_FALLBACK_ENABLED=true
set RAG_MOVIE_AUGMENTATION_ENABLED=false
set RAG_LLM_MODEL=phi3:mini
scripts\run_app.bat
```

### 5) Optional semantic augmentation for movie recommendations

```bat
set RAG_MOVIE_AUGMENTATION_ENABLED=true
scripts\run_app.bat
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


## Contributors

- [Moni](https://github.com/emonhaz)
- [Pramendra Singh](https://github.com/your-github-username)
- [Sajith](https://github.com/sajithkn-alt)
- [Shashank](https://github.com/shashank160790)

