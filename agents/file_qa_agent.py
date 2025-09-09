import os
from google.adk.agents import Agent
from prompts.agent_prompts import FILE_QA_AGENT_PROMPT


file_qa_agent = Agent(
    name="file_qa_agent",
    model=os.getenv("MODEL", "gemini-2.5-pro"),
    description="Answers user questions grounded in uploaded documents with citations.",
    instruction=FILE_QA_AGENT_PROMPT,
) 