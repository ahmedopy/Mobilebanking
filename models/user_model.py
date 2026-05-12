"""
models/user_model.py
All database queries related to users / user_profile.
"""
from models.database import get_db


def get_user_by_id(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user_profile WHERE user_id = %s", (user_id,))
        return cursor.fetchone()


def get_user_by_phone(phone):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user_profile WHERE phone_number = %s", (phone,))
        return cursor.fetchone()


def update_user_profile(user_id, first_name, last_name, dob, email, nid, profile_pic=None):
    db = get_db()
    with db.cursor() as cursor:
        if profile_pic:
            cursor.execute(
                """UPDATE user_profile
                   SET first_name=%s, last_name=%s, dob=%s, email=%s, nid=%s, profile_pic=%s
                   WHERE user_id=%s""",
                (first_name, last_name, dob, email, nid, profile_pic, user_id)
            )
        else:
            cursor.execute(
                """UPDATE user_profile
                   SET first_name=%s, last_name=%s, dob=%s, email=%s, nid=%s
                   WHERE user_id=%s""",
                (first_name, last_name, dob, email, nid, user_id)
            )
    db.commit()


def update_profile_picture(user_id, filename):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE user_profile SET profile_pic = %s WHERE user_id = %s",
            (filename, user_id)
        )
    db.commit()


def get_transaction_limit(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM transaction_limits WHERE user_id = %s", (user_id,))
        return cursor.fetchone()


def set_transaction_limit(user_id, limit_type, limit_amount):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM transaction_limits WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "UPDATE transaction_limits SET limit_type=%s, limit_amount=%s WHERE user_id=%s",
                (limit_type, limit_amount, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO transaction_limits (user_id, limit_type, limit_amount) VALUES (%s, %s, %s)",
                (user_id, limit_type, limit_amount)
            )
    db.commit()


def search_users(query):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """SELECT * FROM user_profile
               WHERE phone_number = %s
               OR first_name LIKE %s
               OR last_name LIKE %s
               OR nid = %s""",
            (query, f"%{query}%", f"%{query}%", query)
        )
        return cursor.fetchall()


def update_user_status(phone, status):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE user_profile SET status = %s WHERE phone_number = %s",
            (status, phone)
        )
    db.commit()
