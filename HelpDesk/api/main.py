import uuid

from fastapi import FastAPI
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from api.schema import ChatRequest, ChatResponse
from helper.agent import root_agent
from mongodb.repository import insert_chat_session

APP_NAME = "IT Help Desk"

app = FastAPI(title="HelpDesk API")

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = str(uuid.uuid4())
    question = request.question

    await insert_chat_session(session_id, question)

    adk_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )

    if adk_session is None:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=session_id,
            session_id=session_id,
        )

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=request.question)],
    )

    final_answer = ""

    async for event in runner.run_async(
        user_id=session_id,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_answer = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_answer = f"Agent escalated: {event.content.parts[0].text}"

    return ChatResponse(
        session_id=session_id,
        ticket_id=None,
        answer=final_answer,
    )