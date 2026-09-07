from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.action import ActionResponse, ActionUpdateRequest
from app.api.dependencies import get_db, get_current_user
from app.schemas.auth import UserClaims
from app.models.action import ActionRecommendation
from app.models.outlet import Outlet

router = APIRouter()

@router.get("", response_model=List[ActionResponse])
async def list_actions(
    user: UserClaims = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ActionRecommendation, Outlet.outlet_name).outerjoin(Outlet, ActionRecommendation.outlet_id == Outlet.id).limit(20)
    res = await db.execute(stmt)
    actions = res.all()
    
    return [
        ActionResponse(
            action_id=str(a.id),
            outlet_id=str(a.outlet_id),
            action_type=a.action_type,
            action_detail=f"{a.action_detail} (Store: {name or 'Outlet'})",
            status=a.status,
            created_at="2026-09-07T00:00:00"
        )
        for a, name in actions
    ]

@router.post("/{action_id}/update", response_model=ActionResponse)
def update_action(action_id: str, req: ActionUpdateRequest, user: UserClaims = Depends(get_current_user)):
    return ActionResponse(
        action_id=action_id,
        outlet_id="OUTLET01",
        action_type="Visit",
        action_detail="Check on device",
        status=req.status,
        created_at="2026-09-07T00:00:00"
    )
