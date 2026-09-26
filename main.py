"""
Main Application Entrypoint.

Configures:
- FastAPI application instance with lifespan DB setup.
- Strict HTTP 400 exception handlers for validation and malformed JSON payloads.
- Static file serving for CSS and client-side JavaScript.
- Inclusion of API and Web (Jinja2) routers.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.controllers import api_router, web_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Initializes database tables and default profile on startup.
    """
    init_db()
    yield


app = FastAPI(
    title="misa.lol Profile Editor",
    description="Standalone mini profile editor trial assessment built with FastAPI and SQLModel.",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# EXCEPTION HANDLERS (Ensuring strict HTTP 400 for contract compliance)
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Intercepts Pydantic validation errors and malformed JSON payloads.
    The trial specification requires HTTP 400 with useful error details,
    rather than default 422 or 500.
    """
    errors = []
    is_malformed_json = False

    for err in exc.errors():
        err_type = err.get("type", "")
        msg = err.get("msg", "Invalid value")

        # Strip Pydantic's "Value error, " prefix if present for cleaner user messages
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]

        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        field_name = ".".join(loc) if loc else "body"

        if "json_invalid" in err_type or "json_decode" in err_type:
            is_malformed_json = True

        errors.append({
            "field": field_name,
            "message": msg,
            "type": err_type
        })

    if is_malformed_json:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Malformed JSON",
                "message": "The request body is not valid JSON.",
                "details": errors
            }
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": "The submitted profile data failed validation.",
            "details": errors
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Ensures standard JSON responses for API HTTP errors.
    """
    # If it's an API request, return JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail}
        )
    # Fallback to default behavior for web views
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# ============================================================================
# STATIC FILES & ROUTERS
# ============================================================================

STATIC_DIR = Path(__file__).resolve().parent / "app" / "views" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount API and Web controllers
app.include_router(api_router)
app.include_router(web_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
