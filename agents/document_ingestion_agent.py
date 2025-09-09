import os
from google.adk.agents import Agent
from google.adk.tools.load_artifacts_tool import load_artifacts_tool
from prompts.agent_prompts import DOC_INGESTION_AGENT_PROMPT


document_ingestion_agent = Agent(
    name="document_ingestion_agent",
    model=os.getenv("MODEL", "gemini-2.5-pro"),
    description="Loads uploaded artifacts, extracts text, and summarizes per file.",
    instruction=DOC_INGESTION_AGENT_PROMPT,
    tools=[load_artifacts_tool],
    output_key="uploaded_docs",
) 