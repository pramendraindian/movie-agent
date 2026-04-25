import sys
import os
from pathlib import Path
# Add parent directory to path so app modules can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))
import uvicorn
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="AI Recommendation Chatbot")
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
