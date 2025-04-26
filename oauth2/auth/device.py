from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime, timedelta
from ..database.operations import (
    get_db, get_client, get_user, create_device_code,
    get_device_code, get_device_code_by_user_code,
    approve_device_code, create_token
)
from ..utils.security import generate_token
from ..models.schemas import DeviceAuthorizationResponse, TokenResponse
from ..config import DEVICE_FLOW

router = APIRouter()

@router.post("/device_authorize", response_model=DeviceAuthorizationResponse)
async def device_authorize(
    client_id: str,
    scope: str = None,
    db = Depends(get_db)
):
    # Validate client
    client = get_client(client_id, db)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Generate codes
    device_code = generate_token()
    user_code = generate_token(6)  # Shorter code for user input
    
    # Create device code
    expires_at = datetime.utcnow() + timedelta(minutes=30)
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

@router.get("/device", response_class=HTMLResponse)
async def device_verification(
    request: Request,
    user_code: str = Query(None),
    db = Depends(get_db)
):
    # If no user_code provided, show the input form
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
    
    # Get device code
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
    
    # Check expiration
    if datetime.utcnow() > datetime.fromisoformat(device_code["expires_at"]):
        return """
        <html>
            <body>
                <h1>Code Expired</h1>
                <p>The code you entered has expired. Please request a new code.</p>
            </body>
        </html>
        """
    
    # Check if already approved
    if device_code["is_approved"]:
        return """
        <html>
            <body>
                <h1>Already Approved</h1>
                <p>This code has already been approved.</p>
            </body>
        </html>
        """
    
    # Show approval form
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

@router.post("/device/approve")
async def approve_device(
    user_code: str,
    db = Depends(get_db)
):
    # Get device code
    device_code = get_device_code_by_user_code(user_code, db)
    if not device_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_code"
        )
    
    # Check expiration
    if datetime.utcnow() > datetime.fromisoformat(device_code["expires_at"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code expired"
        )
    
    # Get test user (in real app, this would be the authenticated user)
    user = get_user("testuser", db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Approve device code
    approve_device_code(user_code, user["id"], db)
    
    return {"status": "approved"}

@router.post("/token", response_model=TokenResponse)
async def device_token(
    grant_type: str,
    device_code: str,
    client_id: str,
    db = Depends(get_db)
):
    if grant_type != "urn:ietf:params:oauth:grant-type:device_code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant_type"
        )
    
    # Get device code
    device = get_device_code(device_code, db)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device_code"
        )
    
    # Check expiration
    if datetime.utcnow() > datetime.fromisoformat(device["expires_at"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code expired"
        )
    
    # Check if approved
    if not device["is_approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization pending"
        )
    
    # Create tokens
    from ..utils.security import create_access_token
    access_token = create_access_token(
        data={"sub": str(device["user_id"])},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = generate_token()
    
    # Store tokens
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