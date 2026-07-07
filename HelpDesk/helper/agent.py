from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm

root_agent = Agent(
    name='helper_agent',
    model=LiteLlm(model="ollama_chat/gemma3:1b"),
    instruction=(
        "You are an in-house IT help desk agent."
        "You use a polite and refined tone."
        "When employees ask questions, use the 'search_faq' tool to retrieve relevant answers."
        "If 'search_faq' returns no results, use the 'create_ticket' tool to generate a ticket for resolving the issue."
        "Do not output emojis, hidden reasoning, or special control characters."
    )
)