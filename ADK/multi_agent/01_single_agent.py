import asyncio
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types  # For creating message Content/Parts

import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)


# Define the get_weather Tool
def get_weather(city: str) -> dict:
    """
    Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Seoul").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {city} ---")
    city_normalized = city.lower().replace(" ", "")

    mock_weather_db = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "seoul": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."}


# Use the model constants
AGENT_MODEL = "ollama_chat/qwen3:4b"


# Define the weather_agent Agent
weather_agent = Agent(
    name="weather_agent_v1",
    model=LiteLlm(model=AGENT_MODEL),
    description="Provides weather information for specific cities.",
    instruction="You are a helpful weather assistant. "
                "When the user asks for the weather in a specific city, "
                "use the 'get_weather' tool to find the information. "
                "If the tool returns an error, inform the user politely. "
                "If the tool is successful, present the weather report clearly.",
    tools=[get_weather],
)


# SessionService stores conversation history & state
session_service = InMemorySessionService()


# Define constants for identifying the interaction context
APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"


async def init_session(app_name: str, user_id: str, session_id: str) -> None:
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )


# Runner orchestrates the agent execution loop
runner = Runner(
    agent=weather_agent,  # The agent we want to run
    app_name=APP_NAME,  # Associates runs with our app
    session_service=session_service,  # Uses our session manager
)


# Define Agent Interaction Function
async def call_agent_async(query: str, runner, user_id, session_id):
    print(f"\n>>> User Query: {query}")

    # Prepare the user's message in ADK format
    content = types.Content(role='user', parts=[types.Part(text=query)])

    final_response_text = "Agent did not produce a final response."

    # run_async executes the agent logic and yields Events
    # We iterate through events to find the final answer
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        # See all events during execution
        print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # is_final_response() marks the concluding message for the turn
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:  # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"

    print(f"<<< Agent Response: {final_response_text}")


# We need an async function to awiat our interaction helper
async def run_conversation():
    # Create the specific session where the conversation will happen
    await init_session(APP_NAME, USER_ID, SESSION_ID)

    await call_agent_async("What is the weather like in London?",
                           runner = runner,
                           user_id = USER_ID,
                           session_id = SESSION_ID)

    await call_agent_async("How about Paris?",
                           runner = runner,
                           user_id = USER_ID,
                           session_id = SESSION_ID)

    await call_agent_async("Tell me the weather in New York.",
                           runner = runner,
                           user_id = USER_ID,
                           session_id = SESSION_ID)


# Execute the conversation using await in an async context
if __name__ == "__main__":
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")
