# agent_service/graph/agent_graph.py

import logging
import uuid
import os
from typing import List, Literal, Annotated
from dotenv import load_dotenv
from google.adk.agents import SequentialAgent, LlmAgent, Agent, BaseAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from tools.weather_tool import weather_tool
from tools.calendar_tool import calendar_tool
from tools.retriever_tool import retriever_tool

logging.basicConfig(level=logging.INFO)
load_dotenv()

# model = "llama3.1:8b"
model = os.getenv("MODEL")
ollama_base_url = os.getenv("BASE_URL")

# Set the OLLAMA_API_BASE environment variable
os.environ["OLLAMA_API_BASE"] = ollama_base_url

APP_NAME = "adk__multi_agent_app"
USER_ID = "1234"
SESSION_ID = str(uuid.uuid4())

llm = LiteLlm(
    model="ollama_chat/" + model,
    api_base=ollama_base_url
)

weather_prompt = """You are a weather assistant. Follow these rules STRICTLY:
1. ONLY answer weather-related questions (e.g., temperature, forecast, rain).
2. Use ONLY the weather_tool to retrieve weather information.
3. DO NOT attempt to answer anything unrelated to weather.
4. After completing your task, ALWAYS transfer back to the supervisor.
"""

calendar_prompt = """You are a calendar assistant. Follow these rules STRICTLY:
1. ONLY answer questions about meetings, schedules, or events.
2. Use ONLY the calendar_tool to check or respond.
3. DO NOT answer anything not related to calendar tasks.
4. After completing your task, ALWAYS transfer back to the supervisor.
"""

retriever_prompt = """You are a document retrieval assistant. Follow these rules STRICTLY:
1. ONLY answer questions about documents, blogs, LLMs, or prompts.
2. Use ONLY the retriever_tool to fetch or summarize.
3. DO NOT respond to anything outside your scope.
4. After completing your task, ALWAYS transfer back to the supervisor.
"""

# Create specialized agents
weather_agent = Agent(
    model=llm,
    tools=[weather_tool],
    name="weather_agent",
    description="Find weather information using weather_tool",
    instruction=weather_prompt
)

calendar_agent = Agent(
    model=llm,
    tools=[calendar_tool],
    name="calendar_agent",
    description="Find meeting or scheduling information using calendar_tool",
    instruction=calendar_prompt
)

retriever_agent = Agent(
    model=llm,
    tools=[retriever_tool],
    name="retriever_agent",
    description="Find local blog or retrival information using retriever_tool",
    instruction=retriever_prompt
)

agents = [weather_agent, calendar_agent, retriever_agent]

# Supervisor agent using standard LangGraph supervisor
supervisor = Agent(
    model=llm,
    name="supervisor_agent",
    description="I coordinate `weather_agent`, `calendar_agent`, and `retriever_agent`",
    instruction="""
            You are a supervisor agent managing `weather_agent`, `calendar_agent`, and `retriever_agent`.

            **Responsibilities:**
            1. Split the user's question into distinct sub-questions using '?' or logical breaks.
            2. For each sub-question:
            - Identify the intent (weather, calendar, documents).
            - Use only ONE specialized agent per sub-question:
                - If about temperature, forecast, rain, etc. → use `weather_agent`.
                - If about meetings, schedules, appointments → use `calendar_agent`.
                - If about documents, blogs, prompts, retrieval → use `retriever_agent`.
            3. For each sub-question, send only the relevant part to the appropriate agent.
            4. Wait for all agent responses.
            5. Use `compile_responses` to merge results.
            6. Use `finalize_response` to polish and format the final message for the user.

            **Strict Rules:**
            - DO NOT answer any sub-question yourself.
            - DO NOT send the same sub-question to multiple agents.
            - DO NOT skip any sub-question.
            - ALWAYS wait for all agent outputs before responding.
            - ALWAYS use `compile_responses` and `finalize_response`.
            - Respond ONLY with `FINISH` when ready to return the final output.
            """,
    sub_agents=agents,
)

# Session and Runner
session_service = InMemorySessionService()
runner = Runner(agent=supervisor, app_name=APP_NAME, session_service=session_service)

# Agent execution wrapper
def llm_call(content: str, user_id: str = USER_ID, session_id: str = str(uuid.uuid4())) -> str:
    """LLM decides whether to call a tool or not"""

    try:
        content = types.Content(role='user', parts=[types.Part(text=content)])
        session_id = str(uuid.uuid4())  # Create a new session ID for each call
        session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
        events = runner.run(user_id=USER_ID, session_id=session_id, new_message=content)

        final_response = None
        for event in events:
            if event.is_final_response():
                final_response = event.content.parts[0].text
                print("Agent Response: ", final_response)

        if not final_response:
            raise ValueError("Empty response from agent")

        return final_response
    except Exception as e:
        logging.error(f"Error in llm_call: {str(e)}")
        raise
