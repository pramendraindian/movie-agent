import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to path so app modules can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router


def _warm_up_services() -> None:
    try:
        from app.services.vision_service import warm_up_vision

        warm_up_vision()
    except Exception as exc:
        print(f"Vision warm-up skipped: {exc}")

    try:
        from app.services.vector_store import get_vector_store

        get_vector_store().retrieve("popular movies", top_k=1)
    except Exception as exc:
        print(f"RAG warm-up skipped: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=_warm_up_services, daemon=True, name="service-warmup").start()
    yield


app = FastAPI(title="AI Recommendation Chatbot", lifespan=lifespan)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
