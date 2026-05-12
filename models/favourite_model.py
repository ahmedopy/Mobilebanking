"""
models/favourite_model.py
Database queries for saved/favourite contacts.
"""
from models.database import get_db


def get_saved_contacts(user_id, search_query=None):
    db = get_db()
    with db.cursor() as cursor:
        if search_query:
            cursor.execute(
                """SELECT * FROM saved_details
                   WHERE user_id = %s AND (name LIKE %s OR phone LIKE %s)""",
                (user_id, f"%{search_query}%", f"%{search_query}%")
            )
        else:
            cursor.execute("SELECT * FROM saved_details WHERE user_id = %s", (user_id,))
        return cursor.fetchall()


def delete_saved_contact(user_id, phone):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "DELETE FROM saved_details WHERE phone = %s AND user_id = %s",
            (phone, user_id)
        )
    db.commit()
