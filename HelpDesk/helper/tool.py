import uuid

from google.adk.tools import ToolContext

from mongodb.repository import find_faq_answer, update_chat_message, update_ticket_id
from mongodb.schema import RoleEnum


async def search_faq(category: str, keywords: list[str], tool_context: ToolContext) -> str:
    """
    Find FAQ content matching the user's question and return the answer.

    Args:
        category (str): Category of user's question
        keywords (list[str]): Keywords extracted from user's question
        tool_context (ToolContext): ToolContext object
    Returns:
        str: FAQ answer
    """
    answer = await find_faq_answer(category, keywords)

    if answer is None:
        content = "There is no matching FAQ."
    else:
        content = answer

    await update_chat_message(tool_context.session.id, category, RoleEnum.TOOL, content)

    return content

async def create_ticket(question: str, category: str, tool_context: ToolContext) -> str:
    """
    Create a ticket(.txt) containing the user's question to be forwarded to the IT team.

    Args:
        question (str): User's question to be used for ticket content
        category (str): Category of user's question
        tool_context (ToolContext): ToolContext object
    """
    ticket_id = str(uuid.uuid4())
    ticket_path = f"{ticket_id}.txt"

    content = (
        f"Ticket ID: {ticket_id}\n"
        f"Category: {category}\n"
        f"Question: {question}\n"
    )

    with open(ticket_path, "x", encoding="utf-8") as file:
        file.write(content)

    await update_ticket_id(tool_context.session.id, ticket_id)

    return f"Ticket created successfully. Ticket ID: {ticket_id}"