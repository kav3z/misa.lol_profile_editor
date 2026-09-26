"""
Controllers package for routing and request handling.
"""
from app.controllers.api_controller import api_router
from app.controllers.web_controller import web_router

__all__ = ["api_router", "web_router"]
