import sqlite3
import traceback
from fastapi import APIRouter, Depends, HTTPException, status

from service.database.operations import get_db
from service.models.schemas import ClientCreate, ClientResponse
from service.utils.security import generate_token


router = APIRouter(prefix="/client", tags=["client"])


@router.post("/oauth/register", response_model=ClientResponse)
async def register_client(client: ClientCreate, db = Depends(get_db)):
    try:
        client_id = generate_token()
        client_secret = generate_token() if client.client_type == "confidential" else ""
        
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO clients 
            (client_id, client_secret, redirect_uris, name, client_type)
            VALUES (?, ?, ?, ?, ?)""",
            (client_id, client_secret, client.redirect_uris, client.name, client.client_type)
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
        "client_id": client_id,
        "name": client.name,
        "client_type": client.client_type,
        "is_active": True
    } 