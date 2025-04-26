from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from ..database.operations import (
    get_db, validate_redirect_uri, get_client, get_user,
    create_authorization_code, get_authorization_code, delete_authorization_code
)
from ..utils.security import verify_code_challenge
from ..models.schemas import TokenResponse

router = APIRouter()

@router.get("/authorize")
async def authorize(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(None),
    state: str = Query(None),
    code_challenge: str = Query(None),
    code_challenge_method: str = Query(None),
    db = Depends(get_db)
):
    # Validate response type
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported response_type"
        )
    
    # Validate client
    client = get_client(client_id, db)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Validate redirect URI
    if not validate_redirect_uri(client_id, redirect_uri, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )
    
    # For simplicity, we'll skip the login and consent screens
    # In a real implementation, you would:
    # 1. Show login page if not authenticated
    # 2. Show consent page with requested scopes
    
    # Get test user (in real app, this would be the authenticated user)
    user = get_user("testuser", db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Create authorization code
    code = create_authorization_code(
        client_id=client_id,
        redirect_uri=redirect_uri,
        user_id=user["id"],
        scope=scope,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        db=db
    )
    
    # Build redirect URL
    params = {"code": code}
    if state:
        params["state"] = state
    
    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return RedirectResponse(url=redirect_url)

@router.post("/token", response_model=TokenResponse)
async def token(
    grant_type: str,
    code: str = None,
    redirect_uri: str = None,
    client_id: str = None,
    client_secret: str = None,
    code_verifier: str = None,
    db = Depends(get_db)
):
    if grant_type != "authorization_code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant_type"
        )
    
    # Get authorization code
    auth_code = get_authorization_code(code, db)
    if not auth_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code"
        )
    
    # Check expiration
    if datetime.utcnow() > datetime.fromisoformat(auth_code["expires_at"]):
        delete_authorization_code(code, db)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code expired"
        )
    
    # Validate client
    client = get_client(client_id, db)
    if not client or client["client_id"] != auth_code["client_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Validate redirect URI
    if redirect_uri != auth_code["redirect_uri"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )
    
    # Validate PKCE
    if auth_code["code_challenge"]:
        if not code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code_verifier required"
            )
        if not verify_code_challenge(code_verifier, auth_code["code_challenge"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code_verifier"
            )
    
    # Create tokens
    from ..utils.security import create_access_token, generate_token
    from datetime import timedelta
    
    access_token = create_access_token(
        data={"sub": str(auth_code["user_id"])},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = generate_token()
    
    # Store tokens
    from ..database.operations import create_token
    create_token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        scope=auth_code["scope"],
        client_id=client_id,
        user_id=auth_code["user_id"],
        db=db
    )
    
    # Delete authorization code
    delete_authorization_code(code, db)
    
    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=1800,
        refresh_token=refresh_token,
        scope=auth_code["scope"]
    ) 