def get_table_definitions():
    return {
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                email TEXT UNIQUE,
                is_active BOOLEAN DEFAULT TRUE
            )
        """,
        "clients": """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT UNIQUE NOT NULL,
                client_secret TEXT NOT NULL,
                redirect_uris TEXT,
                name TEXT NOT NULL,
                client_type TEXT CHECK(client_type IN ('public', 'confidential')) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        """,
        "authorization_codes": """
            CREATE TABLE IF NOT EXISTS authorization_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                client_id TEXT NOT NULL,
                redirect_uri TEXT,
                user_id INTEGER NOT NULL,
                expires_at DATETIME NOT NULL,
                scope TEXT,
                code_challenge TEXT,
                code_challenge_method TEXT
            )
        """,
        "tokens": """
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                access_token TEXT UNIQUE NOT NULL,
                refresh_token TEXT UNIQUE,
                token_type TEXT DEFAULT 'Bearer',
                expires_at DATETIME NOT NULL,
                scope TEXT,
                client_id TEXT NOT NULL,
                user_id INTEGER NOT NULL
            )
        """,
        "device_codes": """
            CREATE TABLE IF NOT EXISTS device_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_code TEXT UNIQUE NOT NULL,
                user_code TEXT UNIQUE NOT NULL,
                client_id TEXT NOT NULL,
                scope TEXT,
                expires_at DATETIME NOT NULL,
                user_id INTEGER,
                verification_uri TEXT NOT NULL,
                interval INTEGER DEFAULT 5,
                is_approved BOOLEAN DEFAULT FALSE
            )
        """
    } 