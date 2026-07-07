from fastapi import FastAPI
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

from api.schema import ChatRequest, ChatResponse
from helper.agent import root_agent

APP_NAME = "IT Help Desk"

app = FastAPI(title="HelpDesk API")

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


@app.post("/chat", response_model=ChatResponse)
async def chat() -> ChatResponse:
    return ChatResponse()