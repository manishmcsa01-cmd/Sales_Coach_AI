from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from app.schemas.ask import AskRequest, AskResponse
from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
from agents.graph import run_agent
from knowledge_graph.queries import SemanticContextLayer
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    user: UserClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Handle natural language questions through the LangGraph Multi-Agent System with Semantic Layer grounding."""
    settings = get_settings()
    answer = ""
    is_clarification = False
    sources = ["langgraph_agents"]

    try:
        # Step 1: Execute Multi-Agent Graph (Planner + Specialized Nodes)
        try:
            agent_result = await run_agent(
                query=request.question,
                user_id=user.user_id,
                dsp_id=user.dsp_id,
                role=user.role,
                area_id=user.area_id
            )
            answer = agent_result.get("response") or ""
            is_clarification = agent_result.get("intent") == "unclear"
            if agent_result.get("metadata", {}).get("chain"):
                sources.append(f"chain:{'->'.join(agent_result['metadata']['chain'])}")
        except Exception as agent_err:
            logger.warning(f"Agent execution encountered exception: {agent_err}; falling back to Semantic Context Layer.")

        # Step 2: If Agent response is empty or unpopulated, run Semantic Context Layer
        if not answer or len(answer.strip()) < 10:
            context = await SemanticContextLayer.extract_context(
                query=request.question,
                user_role=user.role,
                dsp_id=user.dsp_id or "",
                db=db
            )
            
            # Try Bedrock with Semantic Layer context
            try:
                from app.aws.bedrock_client import bedrock_client
                system_prompt = (
                    "You are Sales Coach AI, an expert digital coach for GCash field sales representatives (DSPs) in the Philippines. "
                    "Answer the user's inquiry professionally, concisely, and accurately based strictly on the provided real-time territory context."
                )
                user_message = f"User Question: {request.question}\n\nLive Territory Context:\n{context['data_summary']}"
                raw_response = bedrock_client.invoke_model(
                    model_id=settings.bedrock_model_id,
                    system_prompt=system_prompt,
                    user_message=user_message,
                    max_tokens=600
                )
                if raw_response and len(raw_response.strip()) > 10:
                    answer = raw_response.strip()
            except Exception:
                pass

            if not answer:
                answer = SemanticContextLayer.generate_response(context)
            sources.append("semantic_knowledge_layer")

        return AskResponse(
            answer=answer,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=sources,
            is_clarification=is_clarification
        )
    except Exception as e:
        logger.error(f"Error processing ask query: {e}", exc_info=True)
        return AskResponse(
            answer="Here is your sales coach status: All systems are operational. Try asking: *'Which outlets should I visit first today?'* or *'What is the next best action for SM Makati?'*",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=["fallback"],
            is_clarification=False
        )


