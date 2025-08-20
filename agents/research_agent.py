import os
from google.adk.agents import Agent
from prompts.agent_prompts import RESEARCH_AGENT_PROMPT

research_agent = Agent(
    name="research_agent",
    model=os.getenv("MODEL", "gemini-2.5-pro"),
    description="Reviews and synthesizes search results into a final summary.",
    # The instruction now explicitly uses the state variable for input
    instruction=RESEARCH_AGENT_PROMPT,
)