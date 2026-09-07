from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

from app.schemas.ask import AskRequest, AskResponse
from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
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
    """Handle natural language questions through the Semantic Knowledge Layer."""
    settings = get_settings()

    try:
        # Step 1: Extract multi-table business context via the Semantic Layer
        context = await SemanticContextLayer.extract_context(
            query=request.question,
            user_role=user.role,
            dsp_id=user.dsp_id or "",
            db=db
        )

        answer = ""
        # Step 2: Try Amazon Bedrock if configured and available
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
        except Exception as bedrock_err:
            logger.info(f"Bedrock invocation bypassed ({bedrock_err}); using Semantic Context Generator.")

        # Step 3: Grounded Semantic Fallback
        if not answer:
            answer = SemanticContextLayer.generate_response(context)

        return AskResponse(
            answer=answer,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=["semantic_knowledge_graph", "postgresql_rds"],
            is_clarification=False
        )
    except Exception as e:
        logger.error(f"Error processing ask query: {e}")
        return AskResponse(
            answer="I was unable to retrieve territory details at this moment. Please try asking: *'Which outlets should I visit first today?'*",
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            sources=["fallback"],
            is_clarification=False
        )

