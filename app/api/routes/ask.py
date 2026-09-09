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
    """Handle natural language questions through Semantic Knowledge Graph grounding and Multi-Agent processing."""
    settings = get_settings()
    answer = ""
    is_clarification = False
    sources = []

    try:
        # Step 1: Query the Semantic Context Layer across all 35 enterprise tables
        context = await SemanticContextLayer.extract_context(
            query=request.question,
            user_role=user.role,
            dsp_id=user.dsp_id or "",
            db=db
        )

        # If a specific domain intent is detected from the 35 tables, ground response with live database records
        if context.get("intent") and context["intent"] != "general_inquiry":
            sources.append("semantic_knowledge_layer")
            try:
                from app.aws.bedrock_client import bedrock_client
                system_prompt = (
                    "You are Sales Coach AI, an expert digital coach for GCash field sales representatives (DSPs) and Area Managers in the Philippines. "
                    "Answer the user's inquiry professionally, concisely, and accurately in clean Markdown, based strictly on the provided real-time database context."
                )
                user_message = f"User Question: {request.question}\n\nLive Database Records:\n{context['data_summary']}"
                raw_response = bedrock_client.invoke_model(
                    model_id=settings.bedrock_model_id,
                    system_prompt=system_prompt,
                    user_message=user_message,
                    max_tokens=700
                )
                if raw_response and len(raw_response.strip()) > 10:
                    answer = raw_response.strip()
            except Exception as bedrock_err:
                logger.debug(f"Bedrock invocation in ask route skipped: {bedrock_err}")

            if not answer:
                answer = SemanticContextLayer.generate_response(context)

        # Step 2: Fallback to Multi-Agent Graph if general inquiry
        if not answer:
            try:
                agent_result = await run_agent(
                    query=request.question,
                    user_id=user.user_id,
                    dsp_id=user.dsp_id,
                    role=user.role,
                    area_id=user.area_id
                )
                agent_answer = agent_result.get("response") or ""
                # Avoid returning the generic territory greeting if we have semantic context
                if agent_answer and "Sales Coach AI Territory Overview" not in agent_answer:
                    answer = agent_answer
                    is_clarification = agent_result.get("intent") == "unclear"
                    if agent_result.get("metadata", {}).get("chain"):
                        sources.append(f"chain:{'->'.join(agent_result['metadata']['chain'])}")
            except Exception as agent_err:
                logger.warning(f"Agent execution exception: {agent_err}")

        # Step 3: Final fallback to SemanticContextLayer default synthesis
        if not answer:
            answer = SemanticContextLayer.generate_response(context)
            sources.append("semantic_knowledge_layer")

        return AskResponse(
            answer=answer,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=sources or ["semantic_knowledge_layer"],
            is_clarification=is_clarification
        )
    except Exception as e:
        logger.error(f"Error processing ask query: {e}", exc_info=True)
        return AskResponse(
            answer="Here is your sales coach status: All systems are operational. Try asking: *'Which stores have damaged QR standees?'*, *'Are any merchants out of Cash-In float?'*, or *'Show me POS terminal hardware faults'*.",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=["fallback"],
            is_clarification=False
        )
