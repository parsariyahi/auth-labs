import sqlite3
from datetime import datetime, timedelta
from ..config import DB_FILE

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    from .models import get_table_definitions
    tables = get_table_definitions()
    
    for table_name, create_sql in tables.items():
        cursor.execute(create_sql)
    
    # Add initial test data
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from ..utils.security import get_password_hash
        hashed_password = get_password_hash("password123")
        cursor.execute(
            "INSERT INTO users (username, hashed_password, email) VALUES (?, ?, ?)",
            ("testuser", hashed_password, "test@example.com")
        )
    
    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        # SPA client
        cursor.execute(
            "INSERT INTO clients (client_id, client_secret, redirect_uris, name, client_type) VALUES (?, ?, ?, ?, ?)",
            ("spa_client", "", "http://localhost:8002/callback", "SPA Client", "public")
        )
        # M2M client
        cursor.execute(
            "INSERT INTO clients (client_id, client_secret, name, client_type) VALUES (?, ?, ?, ?)",
            ("m2m_client", "m2m_secret_123", "M2M Client", "confidential")
        )
        # Device client
        cursor.execute(
            "INSERT INTO clients (client_id, client_secret, name, client_type) VALUES (?, ?, ?, ?)",
            ("device_client", "", "Device Client", "public")
        )
    
    conn.commit()
    conn.close()

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

def create_authorization_code(client_id, redirect_uri, user_id, scope, code_challenge, code_challenge_method, db):
    from ..utils.security import generate_token
    code = generate_token()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
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