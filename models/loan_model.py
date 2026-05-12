"""
models/loan_model.py
All database queries related to loans.
"""
from models.database import get_db


def insert_loan_request(user_id, amount, trx_id, duration_months, purpose):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """INSERT INTO loans (user_id, loan_amount, trx_id, duration_months, purpose, status)
               VALUES (%s, %s, %s, %s, %s, 'pending')""",
            (user_id, amount, trx_id, duration_months, purpose)
        )
    db.commit()


def get_pending_loans():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM loans WHERE status = 'pending'")
        return cursor.fetchall()


def approve_loan(trx_id, user_id, amount):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE loans SET status = 'approved' WHERE trx_id = %s",
            (trx_id,)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance + %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()


def deny_loan(trx_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE loans SET status = 'denied' WHERE trx_id = %s",
            (trx_id,)
        )
    db.commit()


def get_active_loans(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM loans WHERE user_id = %s AND status = 'approved'",
            (user_id,)
        )
        return cursor.fetchall()


def pay_loan(trx_id, user_id, amount):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE loans SET status = 'paid' WHERE trx_id = %s AND user_id = %s",
            (trx_id, user_id)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()
