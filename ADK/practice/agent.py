from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm


def get_current_time(city: str) -> dict:
    """Return the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

root_agent = Agent(
    model=LiteLlm(model="ollama_chat/qwen3:4b"),
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction=(
        "Answer user questions to the best of your knowledge"
        "Do not output emojis, hidden reasoning, or special control characters."
    )
)