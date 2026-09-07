from functools import wraps
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

try:
    from aws_xray_sdk.ext.starlette.middleware import XRayMiddleware as StarletteXRayMiddleware
except ImportError:
    StarletteXRayMiddleware = None

def init_xray(service_name: str):
    xray_recorder.configure(service=service_name)
    patch_all()

def trace(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with xray_recorder.in_subsegment(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

class XRayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str = "app"):
        super().__init__(app)
        if StarletteXRayMiddleware:
            self.xray_middleware = StarletteXRayMiddleware(app, recorder=xray_recorder)
        else:
            self.xray_middleware = None
        
    async def dispatch(self, request: Request, call_next):
        if self.xray_middleware:
            return await self.xray_middleware.dispatch(request, call_next)
        return await call_next(request)
