from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.ask import AskRequest, AskResponse
from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
from agents.graph import run_agent
import uuid

router = APIRouter()

@router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest, user: UserClaims = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Handle natural language questions by querying the LangGraph agent."""
    
    agent_response = await run_agent(
        query=request.question,
        user_id=user.user_id,
        role=user.role,
        dsp_id=user.dsp_id,
        area_id=user.area_id
    )
    
    if isinstance(agent_response, dict):
        answer = agent_response.get("response", "I'm sorry, I couldn't process your request.")
    else:
        answer = str(agent_response)
        
    return AskResponse(
        answer=answer,
        conversation_id=request.conversation_id or str(uuid.uuid4()),
        sources=["bedrock_agent"],
        is_clarification=False
    )
