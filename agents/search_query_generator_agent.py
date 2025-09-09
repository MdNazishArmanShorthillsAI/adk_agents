import os
from google.adk.agents import Agent
from prompts.agent_prompts import SEARCH_QUERY_GENERATOR_PROMPT
from tools.nth_search_tool import search_nth_database

search_query_generator_agent = Agent(
    name="search_query_generator_agent",
    model=os.getenv("MODEL", "gemini-2.5-pro"),
    description="Executes a list of search subtasks using the NTH database tool.",
    instruction=SEARCH_QUERY_GENERATOR_PROMPT,
    tools=[search_nth_database],
    output_key="search_results",
)