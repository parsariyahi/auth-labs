from .user import router as user_router
from .client import router as client_router
from .openid import router as openid_router

__all__ = ["user_router", "client_router", "openid_router"] 