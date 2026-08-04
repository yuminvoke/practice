from google.genai import types
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

from helper.agent import root_agent

APP_NAME = "IT Help Desk"

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def run_agent(session_id: str, question: str) -> str:
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
        parts=[types.Part.from_text(text=question)],
    )

    final_answer = ""

    async for event in runner.run_async(
            user_id=session_id,
            session_id=session_id,
            new_message=user_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_answer = "".join(
                    part.text
                    for part in event.content.parts
                    if part.text and not part.thought
                )
            elif event.actions and event.actions.escalate and event.content.parts:
                final_answer = f"Agent escalated: {event.content.parts[0].text}"

    return final_answer