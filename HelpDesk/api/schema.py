from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    session_id: str
    ticket_id: str | None
    answer: str