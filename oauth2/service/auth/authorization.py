import sqlite3
import traceback
from urllib.parse import urlencode, quote
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import datetime

from service.database.operations import (
    get_db, validate_redirect_uri, get_client, get_user, get_user_by_id, authenticate_user,
    create_authorization_code, get_authorization_code, delete_authorization_code
)
from service.utils.security import verify_code_challenge
from service.models.schemas import TokenResponse


router = APIRouter(
    prefix="/oauth2",
    tags=["OAuth2"],
)


@router.get("/authorize")
async def authorize(
    request: Request,
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

        user_id = request.session.get("user_id")
        if not user_id:
            next_url = quote(str(request.url), safe="")
            print("next url \n\n\n\n", next_url)
            login_url = f"/oauth2/login?next={next_url}"
            return RedirectResponse(url=login_url)

        user = get_user_by_id(user_id, db)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        # user = get_user("testuser", db)
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
        
        code = create_authorization_code(
            client_id=client_id,
            redirect_uri=redirect_uri,
            user_id=user["id"],
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            db=db
        )
        
        params = {"code": code}
        if state:
            params["state"] = state
        
        redirect_url = f"{redirect_uri}?{urlencode(params)}"
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
        
        if datetime.now() > datetime.fromisoformat(auth_code["expires_at"]):
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
        
        from service.utils.security import create_access_token, generate_token
        from datetime import timedelta
        
        access_token = create_access_token(
            data={"sub": str(auth_code["user_id"])},
            expires_delta=timedelta(minutes=30)
        )
        refresh_token = generate_token()
        
        from service.database.operations import create_token
        create_token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(minutes=30),
            scope=auth_code["scope"],
            client_id=client_id,
            user_id=auth_code["user_id"],
            db=db
        )
        
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

        
@router.get("/login")
async def login_page(next: str = "/"):
    html_content = """
<html>
    <head>
        <title>Login</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; }
            form { max-width: 300px; margin: auto; }
            input[type=text], input[type=password] {
                width: 100%;
                padding: 12px 20px;
                margin: 8px 0;
                box-sizing: border-box;
            }
            input[type=submit] {
                width: 100%;
                background-color: #4CAF50;
                color: white;
                padding: 14px 20px;
                margin: 8px 0;
                border: none;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h2 style="text-align:center;">Login</h2>
        <form method="post" action="">
            <label>Username:</label><br>
            <input type="text" name="username" required><br>
            <label>Password:</label><br>
            <input type="password" name="password" required><br>
            <input type="submit" value="Login">
        </form>
    </body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db = Depends(get_db)
):
    next_url = request.query_params.get("next")
    user = authenticate_user(username, password, db)
    if not user:
        return HTMLResponse(content="Invalid username or password.", status_code=401)

    request.session["user_id"] = user["id"]

    return RedirectResponse(url=next_url, status_code=302)
