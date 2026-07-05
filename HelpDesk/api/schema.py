from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str | None
    question: str

class ChatResponse(BaseModel):
    session_id: str
    ticket_id: str | None
    answer: str