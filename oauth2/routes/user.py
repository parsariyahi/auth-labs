from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..database.operations import get_db
from ..models.schemas import UserCreate, UserResponse, UserInfoResponse
from ..config import SECRET_KEY, ALGORITHM
import sqlite3

router = APIRouter(prefix="/oauth2", tags=["user"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="oauth2/token")

@router.get("/userinfo", response_model=UserInfoResponse)
async def userinfo(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
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
    except JWTError:
        raise credentials_exception
    
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

@router.post("/register_user", response_model=UserResponse)
async def register_user(user: UserCreate, db = Depends(get_db)):
    from ..utils.security import get_password_hash
    
    hashed_password = get_password_hash(user.password)
    
    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO users 
            (username, hashed_password, email)
            VALUES (?, ?, ?)""",
            (user.username, hashed_password, user.email)
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    return {
        "id": cursor.lastrowid,
        "username": user.username,
        "email": user.email,
        "is_active": True
    } 