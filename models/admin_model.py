"""
models/admin_model.py
Database queries for admin operations.
"""
from models.database import get_db


def get_admin_by_phone(phone):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM admin_profile WHERE phone_number = %s", (phone,))
        return cursor.fetchone()


def get_all_admin_reports():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM admin_reports")
        return cursor.fetchall()


def get_approval_requests():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM admin_profile WHERE status = 'pending'")
        return cursor.fetchall()


def update_admin_status(phone, status):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE admin_profile SET status = %s WHERE phone_number = %s",
            (status, phone)
        )
    db.commit()


def insert_admin_report(user_id, report_type, trx_id, amount):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO admin_reports (user_id, report_type, trx_id, amount) VALUES (%s, %s, %s, %s)",
            (user_id, report_type, trx_id, amount)
        )
    db.commit()
