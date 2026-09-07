from fastapi import HTTPException, Depends
from typing import List
from app.api.dependencies import get_current_user
from app.schemas.auth import UserClaims

def require_role(roles: List[str]):
    def role_checker(user: UserClaims = Depends(get_current_user)):
        user_role = (user.role or "").lower()
        allowed = [r.lower() for r in roles]
        if user_role not in allowed:
            raise HTTPException(status_code=403, detail=f"Forbidden: Insufficient role '{user_role}'")
        return user
    return role_checker

