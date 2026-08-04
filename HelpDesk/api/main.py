from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from api.schema import ChatRequest, ChatResponse
from helper.service import process_chat

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="HelpDesk API")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    session_id, ticket_id, final_answer = await process_chat(request.question)

    return ChatResponse(
        session_id=session_id,
        ticket_id=ticket_id,
        answer=final_answer,
    )