from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api.routes import auth, outlets, briefs, actions, ask, ui, manager, admin
from app.middleware.audit import AuditMiddleware
from app.middleware.tenant import tenant_middleware

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # init_db, build knowledge graph, warm cache
    from app.db.init_db import init_db
    await init_db()
    yield

app = FastAPI(title="Sales Coach AI", lifespan=lifespan)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.aws.xray_helpers import XRayMiddleware
from aws_xray_sdk.core import xray_recorder
app.add_middleware(XRayMiddleware)

app.add_middleware(AuditMiddleware)
app.middleware("http")(tenant_middleware)

@app.on_event("startup")
async def startup_event():
    from app.aws.cloudwatch_client import log_audit_event
    log_audit_event({"event": "Application startup complete", "environment": settings.app_env})

# Static and Templates
import os
static_dir = os.path.join(os.path.dirname(__file__), "ui", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(ui.router)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(outlets.router, prefix="/api/outlets", tags=["outlets"])
app.include_router(briefs.router, prefix="/api/briefs", tags=["briefs"])
app.include_router(actions.router, prefix="/api/actions", tags=["actions"])
app.include_router(ask.router, prefix="/api/ask", tags=["ask"])
app.include_router(manager.router, prefix="/api/manager", tags=["manager"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
