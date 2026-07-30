from google.adk.tools import ToolContext

from mongodb.repository import find_faq_answer, update_chat_message
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

async def create_ticket(question: str, category: str, tool_context: ToolContext):
    """
    Create a ticket(.txt) containing the user's question to be forwarded to the IT team.

    Args:
        question (str): User's question to be used for ticket content
        category (str): Category of user's question
        tool_context (ToolContext): ToolContext object
    """
    ticket_id = tool_context.session.id

    with open(f"{ticket_id}.txt", "w", encoding="utf-8") as f:
        f.write(question)