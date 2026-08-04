import uuid

from helper.runtime import run_agent
from mongodb.repository import insert_chat_session, update_chat_message, find_ticket_id
from mongodb.schema import RoleEnum


async def process_chat(question: str) -> tuple[str, str, str]:
    session_id = str(uuid.uuid4())

    await insert_chat_session(session_id, question)

    agent_answer = await run_agent(session_id, question)

    ticket_id = await find_ticket_id(session_id)

    if ticket_id is not None:
        final_answer = (
            "관련 FAQ를 찾지 못해 IT 담당자에게 문의 티켓을 생성했습니다. "
            f"티켓 ID: {ticket_id}"
        )
    else:
        final_answer = agent_answer

    await update_chat_message(session_id, None, RoleEnum.AGENT, final_answer)

    return session_id, ticket_id, final_answer