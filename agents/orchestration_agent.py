import os
from google.adk.agents import Agent
# AgentTool is the key to this solution
from google.adk.tools.agent_tool import AgentTool
from prompts.agent_prompts import ORCHESTRATION_AGENT_PROMPT
from agents.planning_agent import planning_agent
from agents.search_query_generator_agent import search_query_generator_agent
from agents.research_agent import research_agent

# This is the root agent that coordinates the entire workflow.
# It will use the other agents as tools.
root_agent = Agent(
    name="orchestration_agent",
    # Using a more capable model is better for complex orchestration
    model=os.getenv("MODEL", "gemini-1.5-pro"),
    description="The main orchestrator that uses sub-agents as tools to answer a query.",
    instruction=ORCHESTRATION_AGENT_PROMPT,
    # We provide the sub-agents wrapped as tools.
    tools=[
        AgentTool(agent=planning_agent),
        AgentTool(agent=search_query_generator_agent),
        AgentTool(agent=research_agent),
    ],
)