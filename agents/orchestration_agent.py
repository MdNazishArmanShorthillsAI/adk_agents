import os
from google.adk.agents import Agent
# AgentTool is the key to this solution
from google.adk.tools.agent_tool import AgentTool
from prompts.agent_prompts import ORCHESTRATION_AGENT_PROMPT
from agents.planning_agent import planning_agent
from agents.search_query_generator_agent import search_query_generator_agent
from agents.research_agent import research_agent
from agents.document_ingestion_agent import document_ingestion_agent
from agents.file_qa_agent import file_qa_agent
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from typing import Optional, Any


async def _persist_inline_uploads(*, callback_context: CallbackContext = None, llm_request: LlmRequest = None, **kwargs: Any) -> Optional[types.Content]:
    """Before-model callback that persists inline file uploads as artifacts.

    - Scans the latest user message for inline_data parts.
    - Saves each file to the ArtifactService with a deterministic filename.
    - Records filenames in state.uploaded_files (list).
    - Replaces inline_data with a short text marker in the outgoing request.
    """
    if callback_context is None or llm_request is None:
        return None
    uploaded: list[str] = []
    contents = llm_request.contents if hasattr(llm_request, "contents") else []
    if not contents:
        return None
    # Only look at the last user content part (current turn)
    last = contents[-1]
    if not last or not last.parts:
        return None
    new_parts: list[types.Part] = []
    for idx, part in enumerate(last.parts):
        if part and part.inline_data and part.inline_data.data:
            filename = f"artifact_{callback_context._invocation_context.invocation_id}_{idx}"
            await callback_context.save_artifact(filename=filename, artifact=part)
            uploaded.append(filename)
            new_parts.append(
                types.Part.from_text(
                    text=f"Uploaded file: {filename}. It is saved into artifacts"
                )
            )
        else:
            new_parts.append(part)
    last.parts = new_parts
    if uploaded:
        existing = callback_context.state.get("uploaded_files", []) or []
        callback_context.state.update({"uploaded_files": list({*existing, *uploaded})})
    return None


# This is the root agent that coordinates the entire workflow.
# It will use the other agents as tools.
root_agent = Agent(
    name="orchestration_agent",
    # Using a more capable model is better for complex orchestration
    model=os.getenv("MODEL", "gemini-2.5-pro"),
    description="The main orchestrator that uses sub-agents as tools to answer a query.",
    instruction=ORCHESTRATION_AGENT_PROMPT,
    # We provide the sub-agents wrapped as tools.
    tools=[
        AgentTool(agent=document_ingestion_agent),
        AgentTool(agent=file_qa_agent),
        AgentTool(agent=planning_agent),
        AgentTool(agent=search_query_generator_agent),
        AgentTool(agent=research_agent),
    ],
    before_model_callback=_persist_inline_uploads,
)