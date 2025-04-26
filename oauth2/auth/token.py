from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from ..database.operations import (
    get_db, get_client, get_token_by_refresh_token,
    create_token, delete_token
)
from ..utils.security import create_access_token, generate_token
from ..models.schemas import TokenResponse

router = APIRouter()

@router.post("/token", response_model=TokenResponse)
async def token(
    grant_type: str,
    client_id: str = None,
    client_secret: str = None,
    refresh_token: str = None,
    db = Depends(get_db)
):
    if grant_type not in ["client_credentials", "refresh_token"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant_type"
        )
    
    if grant_type == "client_credentials":
        return await handle_client_credentials(client_id, client_secret, db)
    else:
        return await handle_refresh_token(refresh_token, client_id, db)

async def handle_client_credentials(client_id: str, client_secret: str, db):
    # Validate client
    client = get_client(client_id, db)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Validate client secret for confidential clients
    if client["client_type"] == "confidential" and client["client_secret"] != client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_secret"
        )
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": f"client:{client_id}"},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = generate_token()
    
    # Store tokens
    create_token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        scope="",
        client_id=client_id,
        user_id=None,  # No user for client credentials
        db=db
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=1800,
        refresh_token=refresh_token
    )

async def handle_refresh_token(refresh_token: str, client_id: str, db):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token required"
        )
    
    # Get token
    token = get_token_by_refresh_token(refresh_token, db)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh_token"
        )
    
    # Validate client
    if token["client_id"] != client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Create new tokens
    access_token = create_access_token(
        data={"sub": str(token["user_id"])},
        expires_delta=timedelta(minutes=30)
    )
    new_refresh_token = generate_token()
    
    # Store new tokens
    create_token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="Bearer",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        scope=token["scope"],
        client_id=client_id,
        user_id=token["user_id"],
        db=db
    )
    
    # Delete old token
    delete_token(token["access_token"], db)
    
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=1800,
        refresh_token=new_refresh_token,
        scope=token["scope"]
    ) 