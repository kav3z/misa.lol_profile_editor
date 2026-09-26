"""
Controller Layer: Web View Endpoints (Jinja2 Templates).

Serves:
- GET / -> Profile editor page with live preview and server-side rendered initial state.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.database import get_session
from app.models.profile import UserProfile

web_router = APIRouter(include_in_schema=False)

# Configure Jinja2 templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "views" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@web_router.get("/", response_class=HTMLResponse)
def get_editor_page(request: Request, session: Session = Depends(get_session)):
    """
    Renders the editor view. Passes current profile data to Jinja template
    for server-side rendering and initial form population.
    """
    profile = session.get(UserProfile, 1)
    profile_data = profile.to_dict() if profile else {
        "displayName": "",
        "bio": "",
        "link": {"label": "", "url": ""}
    }

    return templates.TemplateResponse(
        request=request,
        name="editor.html",
        context={
            "profile": profile_data
        }
    )
