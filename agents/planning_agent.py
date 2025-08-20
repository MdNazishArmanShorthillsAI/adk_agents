import os
from google.adk.agents import Agent
from prompts.agent_prompts import PLANNING_AGENT_PROMPT

planning_agent = Agent(
    name="planning_agent",
    model=os.getenv("MODEL", "gemini-1.5-pro"),
    description="Decomposes a complex user query into a list of simple subtasks.",
    instruction=PLANNING_AGENT_PROMPT,
)