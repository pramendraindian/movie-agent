from fastapi import APIRouter
from pydantic import BaseModel
from app.services.intent_service import get_intent_response

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(req: ChatRequest):
    return {"response": get_intent_response(req.message)}
