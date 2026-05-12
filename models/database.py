import pymysql

# ─────────────────────────────────────────────
#  Single shared database connection (mirrors
#  the original app.py connection setup)
# ─────────────────────────────────────────────

_db = None

def get_db():
    """Return the shared database connection (lazy-init)."""
    global _db
    if _db is None:
        _db = pymysql.connect(
            host="localhost",
            user="root",
            password=" 2222 ",         
            database="mobilebanking",
            cursorclass=pymysql.cursors.DictCursor
        )
    return _db

def get_db_connection():
    """Alias used throughout the original codebase."""
    return get_db()
