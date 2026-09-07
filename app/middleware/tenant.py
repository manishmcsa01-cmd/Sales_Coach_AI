from dataclasses import dataclass
from typing import Optional
from contextvars import ContextVar
from fastapi import Request
from jose import jwt
from app.config import get_settings

@dataclass
class TenantContext:
    user_id: str
    role: str
    dsp_id: Optional[str] = None
    area_id: Optional[str] = None
    manager_id: Optional[str] = None

tenant_context: ContextVar[Optional[TenantContext]] = ContextVar("tenant_context", default=None)

def get_tenant() -> Optional[TenantContext]:
    return tenant_context.get()

async def tenant_middleware(request: Request, call_next):
    settings = get_settings()
    auth_header = request.headers.get("Authorization")
    
    context = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            # Decode payload without verifying signature for middleware context
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256", "RS256"], options={"verify_signature": False})
            email = payload.get("email", "") or payload.get("cognito:username", "")
            role = payload.get("custom:role") or payload.get("role")
            if not role:
                groups = payload.get("cognito:groups")
                if isinstance(groups, list) and groups:
                    role = groups[0]
            if not role:
                if "admin" in email.lower():
                    role = "admin"
                elif "manager" in email.lower():
                    role = "manager"
                else:
                    role = "dsp"
            
            context = TenantContext(
                user_id=payload.get("sub") or payload.get("user_id", "unknown"),
                role=str(role).lower(),
                dsp_id=payload.get("custom:dsp_id") or payload.get("dsp_id"),
                area_id=payload.get("custom:area_id") or payload.get("area_id"),
                manager_id=payload.get("custom:manager_id") or payload.get("manager_id")
            )
        except Exception:
            pass

            
    token_id = tenant_context.set(context)
    try:
        response = await call_next(request)
        return response
    finally:
        tenant_context.reset(token_id)
