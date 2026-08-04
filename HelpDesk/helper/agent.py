from pydantic import BaseModel
from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm

from helper.callback import block_unknown_category
from helper.tool import search_faq, create_ticket

root_agent = Agent(
    name='helper_agent',
    model=LiteLlm(
        model="ollama_chat/gemma4:e2b-mlx",
        temperature=0,
    ),
    instruction=(
        "You are an internal IT help desk assistant.\n"
        "Never include the agent name, category, keywords, workflow steps, "
        "tool names, tool arguments, or function calls in the final response.\n"
        "Return only the user-facing answer in Korean. \n"
        "Do not output emojis, hidden reasoning, or special control characters.\n"
        "For every user question, follow this workflow:\n"
        "1. If the question is not IT-related or a tool call is blocked, tell the user the IT help desk cannot resolve it.\n"
        "2. Classify the question into exactly one category: "
        "account, email, network, hardware, software, printer, security, access, or unknown.\n"
        "3. Extract 3 to 5 Korean keywords as nouns from the user's question.\n"
        "4. Call the 'search_faq' tool with the category and keywords.\n"
        "5. If a matching FAQ is found, answer using only the FAQ result.\n"
        "6. If no matching FAQ is found, call the 'create_ticket' tool using the original user's question.\n"
        "7. Return the final response in the required format.\n"
        "8. Never tell the user the request was forwarded unless the create_ticket tool has returned a ticket ID in this turn."
    ),
    tools=[search_faq, create_ticket],
    before_tool_callback=block_unknown_category,
)