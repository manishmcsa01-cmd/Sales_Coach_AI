from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "..", "ui", "templates"))

@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    return RedirectResponse(url="/login")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

@router.get("/outlet/{outlet_id}", response_class=HTMLResponse)
def outlet_page(request: Request, outlet_id: str):
    return templates.TemplateResponse(request, "outlet_detail.html", {"outlet_id": outlet_id})

@router.get("/ask", response_class=HTMLResponse)
def ask_page(request: Request):
    return templates.TemplateResponse(request, "ask.html")

@router.get("/area-summary", response_class=HTMLResponse)
def area_summary_page(request: Request):
    return templates.TemplateResponse(request, "area_summary.html")

@router.get("/dsp-performance", response_class=HTMLResponse)
def dsp_performance_page(request: Request):
    return templates.TemplateResponse(request, "dsp_performance.html")

@router.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(request: Request):
    return templates.TemplateResponse(request, "admin_users.html")

@router.get("/admin/health", response_class=HTMLResponse)
def admin_health_page(request: Request):
    return templates.TemplateResponse(request, "admin_health.html")
