from fastapi import APIRouter, Depends, HTTPException
from ..database.operations import get_db, get_db_dependency, init_db, close_db
import sqlite3
import traceback

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    init_db()

@router.on_event("shutdown")
async def shutdown_event():
    close_db()

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

@router.post("/users")
async def create_user(user: dict, db: sqlite3.Connection = Depends(get_db_dependency)):
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (user["username"], user["email"])
        )
        db.commit()
        return {"message": "User created successfully"}
    except sqlite3.Error as e:
        db.rollback()
        error_summary = {
            "error_type": "DatabaseError",
            "error_message": str(e),
            "error_code": e.sqlite_errorcode if hasattr(e, 'sqlite_errorcode') else None,
            "error_name": e.sqlite_errorname if hasattr(e, 'sqlite_errorname') else None
        }
        raise HTTPException(status_code=500, detail=error_summary)
    except Exception as e:
        db.rollback()
        error_summary = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(status_code=500, detail=error_summary) 