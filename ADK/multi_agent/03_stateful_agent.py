import asyncio
from typing import Optional
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.tool_context import ToolContext
from google.genai import types

import warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)


APP_NAME = "weather_tutorial_agent_team"
USER_ID_STATEFUL = "user_state_demo"
SESSION_ID_STATEFUL = "session_state_demo_001"


def get_weather_stateful(city: str, tool_context: ToolContext) -> dict:
    """Retrieves weather, converts temp unit based on session state."""
    print(f"--- Tool: get_weather_stateful called for {city} ---")

    # Read preference from state
    preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius")
    print(f"--- Tool: Reading state 'user_preference_temperature_unit': {preferred_unit} ---")

    city_normalized = city.lower().replace(" ", "")

    # Mock weather data, always stored in Celsius internally
    mock_weather_db = {
        "newyork": {"temp_c": 25, "condition": "sunny"},
        "london": {"temp_c": 15, "condition": "cloudy"},
        "seoul": {"temp_c": 18, "condition": "light rain"},
    }

    if city_normalized in mock_weather_db:
        data = mock_weather_db[city_normalized]
        temp_c = data["temp_c"]
        condition = data["condition"]

        # Format temperature based on state preference
        if preferred_unit == "Fahrenheit":
            temp_value = (temp_c * 9/5) + 32
            temp_unit = "°F"
        else:
            temp_value = temp_c
            temp_unit = "°C"

        report = f"The weather in {city.capitalize()} is {condition} with a temperature of {temp_value: .0f}{temp_unit}."
        result = {"status": "success", "report": report}
        print(f"--- Tool: Generated report in {preferred_unit}. Result: {result} ---")

        # Example of writing back to state, optional for this tool
        tool_context.state["last_city_checked_stateful"] = city
        print(f"--- Tool: Updated state 'last_city_checked_stateful': {city} ---")

        return result
    else:
        # Handle city not found
        error_msg = f"Sorry, I don't have weather information for '{city}'."
        print(f"--- Tool: City '{city}' not found. ---")
        return {"status": "error", "error_message": error_msg}


def say_hello(name: Optional[str] = None) -> str:
    """
    Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name (str, optional): The name of the person to greet. Defaults to a generic greeting if not provided.

    Returns:
        str: A friendly greeting message.
    """
    if name:
        greeting = f"Hello, {name}!"
        print(f"--- Tool: say_hello called with name: {name} ---")
    else:
        greeting = "Hello there!"
        print(f"--- Tool: say_hello called without specific name (name_arg_value: {name}) ---")
    return greeting


def say_goodbye() -> str:
    """
    Provides a simple farewell message to conclude the conversation.
    """
    print(f"--- Tool: say_goodbye called ---")
    return "Goodbye! Have a great day."


# Use the model constants
AGENT_MODEL = "ollama_chat/gemma4:e2b-mlx"


# Define Greeting Agent
greeting_agent = None
try:
    greeting_agent = Agent(
        model=LiteLlm(model=AGENT_MODEL),
        name="greeting_agent",
        instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting using the 'say_hello' tool. Do nothing else.",
        description="Handles simple greetings and hellos using the 'say_hello' tool.",
        tools=[say_hello],
    )
    print(f"✅ Agent '{greeting_agent.name}' redefined.")
except Exception as e:
    print(f"❌ Could not redefine Greeting agent. Error: {e}")


# Define Farewell Agent
farewell_agent = None
try:
    farewell_agent = Agent(
        model=LiteLlm(model=AGENT_MODEL),
        name="farewell_agent",
        instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message using the 'say_goodbye' tool. Do not perform any other actions.",
        description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.",
        tools=[say_goodbye],
    )
    print(f"✅ Agent '{farewell_agent.name}' redefined.")
except Exception as e:
    print(f"❌ Could not redefine Farewell agent. Error: {e}")


# Create a new session service instance for this sate demonstration
session_service_stateful = InMemorySessionService()
print("✅ New InMemorySessionService created for state demonstration.")


root_agent_stateful = None
runner_root_stateful = None


# Define the updated Root Agent
if greeting_agent and farewell_agent and 'get_weather_stateful' in globals():
    root_agent_model = AGENT_MODEL

    root_agent_stateful = Agent(
        name="weather_agent_v4_stateful",
        model=LiteLlm(model=root_agent_model),
        description="Main agent: Provides weather (state-aware unit), delegates greetings/farewells, saves report to state.",
        instruction="You are the main Weather Agent. Your job is to provide weather using 'get_weather_stateful'. "
                    "The tool will format the temperature based on user preference stored in state. "
                    "Delegate simple greetings to 'greeting_agent' and farewells to 'farewell_agent'. "
                    "Handle only weather requests, greetings, and farewells.",
        tools=[get_weather_stateful],
        sub_agents=[greeting_agent, farewell_agent],
        output_key="last_weather_report"  # Auto-save agent's final weather response
    )
    print(f"✅ Root Agent '{root_agent_stateful.name}' created using stateful tool and output_key.")

    # Create Runner for this Root Agent & new Session Service
    runner_root_stateful = Runner(
        agent=root_agent_stateful,
        app_name=APP_NAME,
        session_service=session_service_stateful
    )
    print(f"✅ Runner created for stateful root agent '{runner_root_stateful.agent.name}' using stateful session service.")
else:
    print("❌ Cannot create stateful root agent. Prerequisites missing.")
    if not greeting_agent: print(" - greeting_agent definition missing.")
    if not farewell_agent: print(" - farewell_agent definition missing.")
    if 'get_weather_stateful' not in globals(): print(" - get_weather_stateful tool missing.")


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
        # print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")

        # is_final_response() marks the concluding message for the turn
        if event.is_final_response():
            if event.content and event.content.parts:
                # Assuming text response in the first part
                final_response_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:  # Handle potential errors/escalations
                final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"

    print(f"<<< Agent Response: {final_response_text}")


# Interact to test state flow and output_key
if 'runner_root_stateful' in globals() and runner_root_stateful:
    # Define the main async function for the stateful conversation logic
    async def run_stateful_conversation():
        # Define initial state data, user prefers Celsius initially
        initial_state = {
            "user_preference_temperature_unit": "Celsius"
        }

        # Create the session, providing the initial state
        await session_service_stateful.create_session(
            app_name=APP_NAME,
            user_id=USER_ID_STATEFUL,
            session_id=SESSION_ID_STATEFUL,
            state=initial_state,
        )
        print(f"✅ Session '{SESSION_ID_STATEFUL}' created for user '{USER_ID_STATEFUL}'.")

        # Verify the initial state was se correctly
        retrieved_session = await session_service_stateful.get_session(
            app_name=APP_NAME,
            user_id=USER_ID_STATEFUL,
            session_id=SESSION_ID_STATEFUL,
        )

        print("\n--- Initial Session State ---")
        if retrieved_session:
            print(retrieved_session.state)
        else:
            print("Error: Could not retrieve session.")

        print("\n---Testing State: Temp Unit Conversion & output_key ---")

        # 1. Check weather (Use initial state: Celsius)
        print("--- Turn 1: Requesting weather in London (expect Celsius) ---")
        await call_agent_async(
            query="What's the weather in London?",
            runner=runner_root_stateful,
            user_id=USER_ID_STATEFUL,
            session_id=SESSION_ID_STATEFUL
        )

        # 2. Manually update state preference to Fahrenheit (Directly modify storage)
        print("\n--- Manually Updating State: Setting unit to Fahrenheit ---")
        try:
            # Access the internal storage directly
            # In production with persistent services, you would typically update state via agent actions or specific service APIs
            stored_session = session_service_stateful.sessions[APP_NAME][USER_ID_STATEFUL][SESSION_ID_STATEFUL]
            stored_session.state["user_preference_temperature_unit"] = "Fahrenheit"
            print(f"--- Stored session state updated. Current 'user_preference_temperature_unit': {stored_session.state.get('user_preference_temperature_unit', 'Not Set')} ---")
        except KeyError:
            print(
                f"--- Error: Could not retrieve session '{SESSION_ID_STATEFUL}' from internal storage for user '{USER_ID_STATEFUL}' in app '{APP_NAME}' to update state. Check IDs and if session was created. ---")
        except Exception as e:
            print(f"--- Error updating internal session state: {e} ---")

        # 3. Check weather again (Tool should now use Fahrenheit)
        # This will also update 'last_weather_report' via output_key
        print("\n--- Turn 2: Requesting weather in New York (expect Fahrenheit) ---")
        await call_agent_async(
            query="Tell me the weather in New York.",
            runner=runner_root_stateful,
            user_id=USER_ID_STATEFUL,
            session_id=SESSION_ID_STATEFUL
        )

        # 4. Test basic delegation
        # This will update 'last_weather_report' again, overwriting the NY weather report
        print("\n--- Turn 3: Sending a greeting ---")
        await call_agent_async(
            query="Hi!",
            runner=runner_root_stateful,
            user_id=USER_ID_STATEFUL,
            session_id=SESSION_ID_STATEFUL
        )

        print("\n--- Inspecting Final Session State ---")
        final_session = await session_service_stateful.get_session(
            app_name=APP_NAME,
            user_id=USER_ID_STATEFUL,
            session_id=SESSION_ID_STATEFUL
        )

        if final_session:
            # Use .get() for safer access to potentially missing keys
            print(f"Final Preference: {final_session.state.get('user_preference_temperature_unit', 'Not Set')}")
            print(f"Final Last Weather Report (from output_key): {final_session.state.get('last_weather_report', 'Not Set')}")
            print(f"Final Last City Checked (by tool): {final_session.state.get('last_city_checked_stateful', 'Not Set')}")

            # Print full state for detailed view
            # print(f"Full State Dict: {final_session.state}")
        else:
            print("\n❌ Error: Could not retrieve final session state.")

    # Execute the 'run_stateful_conversation' async function
    if __name__ == "__main__":  # Ensures this runs only when script is executed directly
        print("Executing using 'asyncio.run()' (for standard Python scripts)...")
        try:
            asyncio.run(run_stateful_conversation())
        except Exception as e:
            print(f"An error occurred: {e}")
else:
    print("\n⚠️ Skipping state test conversation. Stateful root agent runner ('runner_root_stateful') is not available.")