# agent_service/app.py
import os
import logging
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from graph.agent_graph import llm_call
# from slowapi import Limiter
# from slowapi.util import get_remote_address

# Load env variables
load_dotenv()
logging.basicConfig(level=logging.INFO)

# FastAPI app
# limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class InputMessage(BaseModel):
    text: str

class OutputMessage(BaseModel):
    reply: str

user_sessions = {}  # In-memory storage for user sessions

def get_user_id(request: Request):
    # Simple way to identify a user (can be improved with authentication)
    return request.client.host

@app.post("/chat", response_model=OutputMessage)
def chat(input_msg: InputMessage, request: Request):
    try:
        user_id = get_user_id(request)
        if user_id not in user_sessions:
            user_sessions[user_id] = str(uuid.uuid4())
        session_id = user_sessions[user_id]

        logging.info(f"Received message from user {user_id} (session {session_id}): {input_msg.text}")
        reply = llm_call(content=input_msg.text, user_id=user_id, session_id=session_id)
        return {"reply": reply}
    except Exception as e:
        logging.exception("Chat processing failed.")
        raise HTTPException(status_code=500, detail="Unexpected server error.")
    
@app.get("/")
def health():
    return {"status": "agent running"}

@app.get("/info")
def info():
    return {"status": "ok"}

@app.post("/runs/batch")
def run_batch():
    return {"status": "OK", "message": "Batch endpoint placeholder"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

