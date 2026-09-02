from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time
from app.middleware.tenant import get_tenant

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        tenant = get_tenant()
        user_id = tenant.user_id if tenant else "anonymous"
        role = tenant.role if tenant else "none"
        
        from app.aws.cloudwatch_client import log_audit_event
        from aws_xray_sdk.core import xray_recorder
        
        trace_id = None
        try:
            entity = xray_recorder.get_trace_entity()
            if entity:
                trace_id = entity.trace_id
        except Exception:
            pass

        log_audit_event({
            "path": request.url.path,
            "method": request.method,
            "user_id": user_id,
            "role": role,
            "status_code": response.status_code,
            "latency": process_time,
            "trace_id": trace_id
        })
            
        return response
