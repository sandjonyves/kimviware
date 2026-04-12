"""Pages HTML (dashboard)."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from kimvieware_orchestrator.paths import get_orchestrator_root

templates = Jinja2Templates(directory=str(get_orchestrator_root() / "templates"))

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {"request": request, "page_title": "KIMVIEware Pro - Dashboard"},
    )
