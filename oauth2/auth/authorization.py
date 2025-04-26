from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from ..database.operations import (
    get_db, validate_redirect_uri, get_client, get_user,
    create_authorization_code, get_authorization_code, delete_authorization_code
)
from ..utils.security import verify_code_challenge
from ..models.schemas import TokenResponse
import sqlite3
import traceback
from urllib.parse import urlencode

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
    try:
        # Validate response type
        if response_type != "code":
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Unsupported response_type",
                "details": f"response_type must be 'code', got '{response_type}'"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Validate client
        client = get_client(client_id, db)
        if not client:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Invalid client_id",
                "details": f"Client '{client_id}' not found"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Validate redirect URI
        if not validate_redirect_uri(client_id, redirect_uri, db):
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Invalid redirect_uri",
                "details": f"Redirect URI '{redirect_uri}' not registered for client '{client_id}'"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Get test user (in real app, this would be the authenticated user)
        user = get_user("testuser", db)
        if not user:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "User not found",
                "details": "Test user 'testuser' not found"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
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
        print(redirect_url)
        return RedirectResponse(url=redirect_url)
    except sqlite3.Error as e:
        error_summary = {
            "error_type": "DatabaseError",
            "error_message": str(e),
            "error_code": e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else None,
            "error_name": e.sqlite_errorname if hasattr(e, 'sqlite_errorname') else None
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_summary)
    except Exception as e:
        error_summary = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_summary)

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
    try:
        if grant_type != "authorization_code":
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Unsupported grant_type",
                "details": f"grant_type must be 'authorization_code', got '{grant_type}'"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Get authorization code
        auth_code = get_authorization_code(code, db)
        if not auth_code:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Invalid authorization code",
                "details": f"Code '{code}' not found"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Check expiration
        if datetime.utcnow() > datetime.fromisoformat(auth_code["expires_at"]):
            delete_authorization_code(code, db)
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Authorization code expired",
                "details": f"Code '{code}' expired at {auth_code['expires_at']}"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Validate client
        client = get_client(client_id, db)
        if not client or client["client_id"] != auth_code["client_id"]:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Invalid client_id",
                "details": f"Client '{client_id}' not found or doesn't match authorization code"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Validate redirect URI
        if redirect_uri != auth_code["redirect_uri"]:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Invalid redirect_uri",
                "details": f"Redirect URI '{redirect_uri}' doesn't match authorization code"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        # Validate PKCE
        if auth_code["code_challenge"]:
            if not code_verifier:
                error_summary = {
                    "error_type": "ValidationError",
                    "error_message": "code_verifier required",
                    "details": "PKCE code_verifier is required for this authorization code"
                }
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_summary
                )
            if not verify_code_challenge(code_verifier, auth_code["code_challenge"]):
                error_summary = {
                    "error_type": "ValidationError",
                    "error_message": "Invalid code_verifier",
                    "details": "PKCE code_verifier doesn't match code_challenge"
                }
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_summary
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
    except sqlite3.Error as e:
        error_summary = {
            "error_type": "DatabaseError",
            "error_message": str(e),
            "error_code": e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else None,
            "error_name": e.sqlite_errorname if hasattr(e, 'sqlite_errorname') else None
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_summary)
    except Exception as e:
        error_summary = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_summary) 