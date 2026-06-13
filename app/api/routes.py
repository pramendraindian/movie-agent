from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.context_manager import get_context_manager
from app.services.intent_service import get_intent_response

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = ""
    session_id: Optional[str] = None
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded poster image for visual movie understanding",
    )


@router.post("/chat")
def chat(req: ChatRequest):
    if not req.message and not req.image_base64:
        return {"response": "Please send a message or upload a movie poster.", "movies": []}
    return get_intent_response(
        req.message or "What movie is this poster? Recommend similar films.",
        session_id=req.session_id,
        image_base64=req.image_base64,
    )


@router.delete("/session/{session_id}")
def clear_session(session_id: str):
    get_context_manager().clear(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.get("/health")
def health():
    return {"status": "ok", "agentic_rag": True}
