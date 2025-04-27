import sqlite3
import traceback
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta

from service.database.operations import (
    get_db, get_client, get_user, create_device_code,
    get_device_code, get_device_code_by_user_code,
    approve_device_code, create_token
)
from service.utils.security import generate_token
from service.models.schemas import DeviceAuthorizationResponse, TokenResponse
from service.config import DEVICE_FLOW


router = APIRouter(
    prefix="/device",
    tags=["Device"],
)


@router.post("/authorize", response_model=DeviceAuthorizationResponse)
async def device_authorize(
    client_id: str,
    scope: str = None,
    db = Depends(get_db)
):
    try:
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
        
        device_code = generate_token()
        user_code = generate_token(6)  # Shorter code for user input
        
        expires_at = datetime.now() + timedelta(minutes=30)
        create_device_code(
            device_code=device_code,
            user_code=user_code,
            client_id=client_id,
            scope=scope,
            expires_at=expires_at,
            verification_uri=DEVICE_FLOW["verification_uri"],
            interval=DEVICE_FLOW["interval"],
            db=db
        )
        
        return DeviceAuthorizationResponse(
            device_code=device_code,
            user_code=user_code,
            verification_uri=DEVICE_FLOW["verification_uri"],
            verification_uri_complete=f"{DEVICE_FLOW['verification_uri']}?user_code={user_code}",
            expires_in=1800,
            interval=DEVICE_FLOW["interval"]
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


@router.get("/verify", response_class=HTMLResponse)
async def device_verification(
    request: Request,
    user_code: str = Query(None),
    db = Depends(get_db)
):
    if not user_code:
        return """
        <html>
            <body>
                <h1>Device Authorization</h1>
                <form method="get">
                    <label for="user_code">Enter your code:</label>
                    <input type="text" id="user_code" name="user_code" required>
                    <button type="submit">Submit</button>
                </form>
            </body>
        </html>
        """
    
    device_code = get_device_code_by_user_code(user_code, db)
    if not device_code:
        return """
        <html>
            <body>
                <h1>Invalid Code</h1>
                <p>The code you entered is invalid. Please try again.</p>
                <a href="/device">Back</a>
            </body>
        </html>
        """
    
    if datetime.now() > datetime.fromisoformat(device_code["expires_at"]):
        return """
        <html>
            <body>
                <h1>Code Expired</h1>
                <p>The code you entered has expired. Please request a new code.</p>
            </body>
        </html>
        """
    
    if device_code["is_approved"]:
        return """
        <html>
            <body>
                <h1>Already Approved</h1>
                <p>This code has already been approved.</p>
            </body>
        </html>
        """
    
    return f"""
    <html>
        <body>
            <h1>Approve Device</h1>
            <p>Code: {user_code}</p>
            <form method="post" action="/device/approve">
                <input type="hidden" name="user_code" value="{user_code}">
                <button type="submit">Approve</button>
            </form>
        </body>
    </html>
    """


@router.post("/approve")
async def approve_device(
    user_code: str,
    db = Depends(get_db)
):
    try:
        device_code = get_device_code_by_user_code(user_code, db)
        if not device_code:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Invalid user_code",
                "details": f"User code '{user_code}' not found"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        if datetime.now() > datetime.fromisoformat(device_code["expires_at"]):
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Code expired",
                "details": f"Code '{user_code}' expired at {device_code['expires_at']}"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
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
        
        approve_device_code(user_code, user["id"], db)
        
        return {"status": "approved"}
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
async def device_token(
    grant_type: str,
    device_code: str,
    client_id: str,
    db = Depends(get_db)
):
    try:
        if grant_type != "urn:ietf:params:oauth:grant-type:device_code":
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Unsupported grant_type",
                "details": f"grant_type must be 'urn:ietf:params:oauth:grant-type:device_code', got '{grant_type}'"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        device = get_device_code(device_code, db)
        if not device:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Invalid device_code",
                "details": f"Device code '{device_code}' not found"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        if datetime.now() > datetime.fromisoformat(device["expires_at"]):
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Code expired",
                "details": f"Code '{device_code}' expired at {device['expires_at']}"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        if not device["is_approved"]:
            error_summary = {
                "error_type": "ValidationError",
                "error_message": "Authorization pending",
                "details": "Device code has not been approved yet"
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_summary
            )
        
        from service.utils.security import create_access_token
        access_token = create_access_token(
            data={"sub": str(device["user_id"])},
            expires_delta=timedelta(minutes=30)
        )
        refresh_token = generate_token()
        
        create_token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            scope=device["scope"],
            client_id=client_id,
            user_id=device["user_id"],
            db=db
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=1800,
            refresh_token=refresh_token,
            scope=device["scope"]
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