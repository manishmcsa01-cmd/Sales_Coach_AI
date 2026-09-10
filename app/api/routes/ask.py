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

    # Application-level control: disallow empty or trivial spam queries to avoid wasted LLM processing
    cleaned_question = (request.question or "").strip()
    if len(cleaned_question) < 2:
        return AskResponse(
            answer="Please ask a specific question about your sales territory, merchant performance, or daily visit priorities.",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=["input_validation_guardrail"],
            is_clarification=False
        )

    try:
        # Step 1: Query the Semantic Context Layer across all 35 enterprise tables
        context = await SemanticContextLayer.extract_context(
            query=cleaned_question,
            user_role=user.role,
            dsp_id=user.dsp_id or "",
            db=db
        )

        # Step 2: Invoke Bedrock Foundation Model (Claude 3.5 Sonnet / Nova) directly with question + database grounding
        try:
            from app.aws.bedrock_client import bedrock_client
            system_prompt = (
                "You are Sales Coach AI, an intelligent digital coach and advisor for GCash field sales representatives (DSPs), "
                "merchants, and Area Managers in the Philippines. "
                "Answer the user's question directly, accurately, and conversationally in clean Markdown. "
                "If the question is about GCash operations, merchants, POS terminals, QR standees, liquidity float, or sales territory, "
                "use the live database records provided below to ground your answer. "
                "If the question is a general question, greeting, or general knowledge inquiry, answer it clearly and concisely."
            )
            data_context = context.get("data_summary", "")
            user_message = f"User Question: {request.question}\n\nLive Database & Territory Context:\n{data_context}"
            
            raw_response = bedrock_client.invoke_model(
                model_id=settings.bedrock_model_id,
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=1024
            )
            if raw_response and len(raw_response.strip()) > 5:
                answer = raw_response.strip()
                sources.append(f"bedrock:{settings.bedrock_model_id}")
        except Exception as bedrock_err:
            logger.warning(f"Bedrock invocation in ask route encountered an issue: {bedrock_err}", exc_info=True)
            # Surface Bedrock connection diagnostic directly to help user verify AWS IAM / model permissions
            bedrock_diagnostic = f"⚠️ **Bedrock LLM Error**: `{type(bedrock_err).__name__}: {str(bedrock_err)}`"

        # Step 3: Multi-Agent Graph fallback if Bedrock was unavailable
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
                if agent_answer and "Sales Coach AI Territory Overview" not in agent_answer:
                    answer = agent_answer
                    is_clarification = agent_result.get("intent") == "unclear"
                    if agent_result.get("metadata", {}).get("chain"):
                        sources.append(f"chain:{'->'.join(agent_result['metadata']['chain'])}")
            except Exception as agent_err:
                logger.warning(f"Agent execution exception: {agent_err}")

        # Step 4: Final fallback to SemanticContextLayer deterministic synthesis
        if not answer:
            answer = SemanticContextLayer.generate_response(context)
            if 'bedrock_diagnostic' in locals() and bedrock_diagnostic:
                answer += f"\n\n---\n{bedrock_diagnostic}"
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
