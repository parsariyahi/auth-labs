from fastapi import APIRouter, Depends, HTTPException, status
from ..database.operations import get_db
from ..models.schemas import ClientCreate, ClientResponse
from ..utils.security import generate_token
import sqlite3

router = APIRouter(prefix="/oauth2", tags=["client"])

@router.post("/register_client", response_model=ClientResponse)
async def register_client(client: ClientCreate, db = Depends(get_db)):
    client_id = generate_token()
    client_secret = generate_token() if client.client_type == "confidential" else ""
    
    cursor = db.cursor()
    try:
        cursor.execute(
            """INSERT INTO clients 
            (client_id, client_secret, redirect_uris, name, client_type)
            VALUES (?, ?, ?, ?, ?)""",
            (client_id, client_secret, client.redirect_uris, client.name, client.client_type)
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID already exists"
        )
    
    return {
        "id": cursor.lastrowid,
        "client_id": client_id,
        "name": client.name,
        "client_type": client.client_type,
        "is_active": True
    } 