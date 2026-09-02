from fastapi import HTTPException
from typing import List
from app.middleware.tenant import get_tenant

def require_role(roles: List[str]):
    def role_checker():
        tenant = get_tenant()
        if not tenant:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if tenant.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        return tenant
    return role_checker
