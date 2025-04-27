from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from service.database.operations import init_db
from service.auth import auth_router, token_router, device_router

from service.routes import user_router, client_router, openid_router

init_db("service/oauth_provider.db")

app = FastAPI(title="OAuth2 Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.include_router(token_router)
app.include_router(device_router)
app.include_router(auth_router)

app.include_router(user_router)
app.include_router(client_router)
app.include_router(openid_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
