from fastapi import APIRouter, Depends
from typing import List
from app.schemas.action import ActionResponse, ActionUpdateRequest
from app.api.dependencies import get_current_user
from app.schemas.auth import UserClaims

router = APIRouter()

@router.get("", response_model=List[ActionResponse])
def list_actions(user: UserClaims = Depends(get_current_user)):
    return []

@router.post("/{action_id}/update", response_model=ActionResponse)
def update_action(action_id: str, req: ActionUpdateRequest, user: UserClaims = Depends(get_current_user)):
    return ActionResponse(
        action_id=action_id,
        outlet_id="OUTLET01",
        action_type="Visit",
        action_detail="Check on device",
        status=req.status,
        created_at="2026-08-31T00:00:00"
    )
