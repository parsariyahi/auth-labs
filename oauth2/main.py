# oauth_provider.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from oauth2.database.operations import init_db
from oauth2.auth.authorization import router as auth_router
from oauth2.auth.token import router as token_router
from oauth2.auth.device import router as device_router
from oauth2.routes import user_router, client_router, openid_router

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(title="OAuth2 Provider")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(token_router)
app.include_router(device_router)
app.include_router(user_router)
app.include_router(client_router)
app.include_router(openid_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
