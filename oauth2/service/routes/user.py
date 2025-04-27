import sqlite3
import traceback
from jose import JWTError, jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from service.database.operations import get_db
from service.models.schemas import UserCreate, UserResponse, UserInfoResponse
from service.config import SECRET_KEY, ALGORITHM
from service.database.operations import get_db_dependency


router = APIRouter(prefix="/oauth2", tags=["user"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth2/token")


@router.get("/users/info", response_model=UserInfoResponse)
async def userinfo(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError as e:
            error_summary = {
                "error_type": "JWTError",
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_summary,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # For client credentials flow, the "sub" is the client ID
        if user_id.startswith("client:"):
            return {"sub": user_id}
        
        # For normal user tokens, fetch user info
        cursor = db.cursor()
        cursor.execute(
            "SELECT username, email FROM users WHERE id = ?",
            (int(user_id),)
        )
        user = cursor.fetchone()
        
        if not user:
            raise credentials_exception
        
        return {
            "sub": user_id,
            "username": user["username"],
            "email": user["email"]
        }
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


@router.post("/users/register", response_model=UserResponse)
async def register_user(user: UserCreate, db = Depends(get_db)):
    try:
        from service.utils.security import get_password_hash
        
        hashed_password = get_password_hash(user.password)
        
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO users 
            (username, hashed_password, email)
            VALUES (?, ?, ?)""",
            (user.username, hashed_password, user.email)
        )
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        error_summary = {
            "error_type": "DatabaseError",
            "error_message": str(e),
            "error_code": e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else None,
            "error_name": e.sqlite_errorname if hasattr(e, 'sqlite_errorname') else None
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_summary)
    except Exception as e:
        db.rollback()
        error_summary = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_summary)
    
    return {
        "id": cursor.lastrowid,
        "username": user.username,
        "email": user.email,
        "is_active": True
    } 


@router.get("/users")
async def get_users(db: sqlite3.Connection = Depends(get_db_dependency)):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return users
    except sqlite3.Error as e:
        error_summary = {
            "error_type": "DatabaseError",
            "error_message": str(e),
            "error_code": e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else None,
            "error_name": e.sqlite_errorname if hasattr(e, 'sqlite_errorname') else None
        }
        raise HTTPException(status_code=500, detail=error_summary)
    except Exception as e:
        error_summary = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_summary)


# @router.post("/users")
# async def create_user(user: dict, db: sqlite3.Connection = Depends(get_db_dependency)):
#     try:
#         cursor = db.cursor()
#         cursor.execute(
#             "INSERT INTO users (username, email) VALUES (?, ?)",
#             (user["username"], user["email"])
#         )
#         db.commit()
#         return {"message": "User created successfully"}
#     except sqlite3.Error as e:
#         db.rollback()
#         error_summary = {
#             "error_type": "DatabaseError",
#             "error_message": str(e),
#             "error_code": e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else None,
#             "error_name": e.sqlite_errorname if hasattr(e, 'sqlite_errorname') else None
#         }
#         raise HTTPException(status_code=500, detail=error_summary)
#     except Exception as e:
#         db.rollback()
#         error_summary = {
#             "error_type": type(e).__name__,
#             "error_message": str(e),
#             "traceback": traceback.format_exc()
#         }
#         raise HTTPException(status_code=500, detail=error_summary) 
