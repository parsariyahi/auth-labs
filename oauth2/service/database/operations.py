import os
import sqlite3
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from service.config import DB_FILE
from service.utils.security import verify_password

local_storage = threading.local()

Base = declarative_base()

def get_db():
    if not hasattr(local_storage, 'connection'):
        local_storage.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        local_storage.connection.row_factory = sqlite3.Row
    return local_storage.connection

def close_db():
    if hasattr(local_storage, 'connection'):
        local_storage.connection.close()
        del local_storage.connection

def init_db(db_path="service/oauth_provider.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

def validate_redirect_uri(client_id, redirect_uri, db):
    cursor = db.cursor()
    cursor.execute("SELECT redirect_uris FROM clients WHERE client_id = ?", (client_id,))
    client = cursor.fetchone()
    if not client:
        return False
    allowed_uris = client["redirect_uris"].split(",") if client["redirect_uris"] else []
    return redirect_uri in allowed_uris

def get_client(client_id, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
    return cursor.fetchone()

def get_user(username, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cursor.fetchone()

def get_user_by_id(id, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    return cursor.fetchone()

def authenticate_user(username: str, password: str, db):
    user = get_user(username, db)
    if user and verify_password(password, user["hashed_password"]):
        return user
    return None

def create_authorization_code(client_id, redirect_uri, user_id, scope, code_challenge, code_challenge_method, db):
    from service.utils.security import generate_token
    code = generate_token()
    expires_at = datetime.now() + timedelta(minutes=10)
    
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO authorization_codes 
           (code, client_id, redirect_uri, user_id, expires_at, scope, code_challenge, code_challenge_method)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (code, client_id, redirect_uri, user_id, expires_at, scope, code_challenge, code_challenge_method)
    )
    db.commit()
    return code

def get_authorization_code(code, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM authorization_codes WHERE code = ?", (code,))
    return cursor.fetchone()

def delete_authorization_code(code, db):
    cursor = db.cursor()
    cursor.execute("DELETE FROM authorization_codes WHERE code = ?", (code,))
    db.commit()

def create_token(access_token, refresh_token, token_type, expires_at, scope, client_id, user_id, db):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO tokens 
           (access_token, refresh_token, token_type, expires_at, scope, client_id, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (access_token, refresh_token, token_type, expires_at, scope, client_id, user_id)
    )
    db.commit()

def get_token(access_token, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tokens WHERE access_token = ?", (access_token,))
    return cursor.fetchone()

def get_token_by_refresh_token(refresh_token, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tokens WHERE refresh_token = ?", (refresh_token,))
    return cursor.fetchone()

def delete_token(access_token, db):
    cursor = db.cursor()
    cursor.execute("DELETE FROM tokens WHERE access_token = ?", (access_token,))
    db.commit()

def create_device_code(device_code, user_code, client_id, scope, expires_at, verification_uri, interval, db):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO device_codes 
           (device_code, user_code, client_id, scope, expires_at, verification_uri, interval)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (device_code, user_code, client_id, scope, expires_at, verification_uri, interval)
    )
    db.commit()

def get_device_code(device_code, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM device_codes WHERE device_code = ?", (device_code,))
    return cursor.fetchone()

def get_device_code_by_user_code(user_code, db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM device_codes WHERE user_code = ?", (user_code,))
    return cursor.fetchone()

def approve_device_code(user_code, user_id, db):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE device_codes SET is_approved = TRUE, user_id = ? WHERE user_code = ?",
        (user_id, user_code)
    )
    db.commit()

@contextmanager
def get_db_context():
    db = get_db()
    try:
        yield db
    finally:
        pass  # Don't close the connection here, it's managed by the thread-local storage

def get_db_dependency():
    with get_db_context() as db:
        yield db 