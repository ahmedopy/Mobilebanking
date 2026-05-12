"""
models/investment_model.py
All database queries related to investments.
"""
from models.database import get_db


def get_investment_options():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM investment_options")
        return cursor.fetchall()


def get_latest_investment(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM investment_user WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        return cursor.fetchone()


def insert_investment(user_id, option_id, amount, trx_id, maturity_date):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """INSERT INTO investment_user
               (user_id, option_id, amount, trx_id, maturity_date, status)
               VALUES (%s, %s, %s, %s, %s, 'active')""",
            (user_id, option_id, amount, trx_id, maturity_date)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()


def get_current_investments(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM investment_user WHERE user_id = %s AND status = 'active'",
            (user_id,)
        )
        return cursor.fetchall()


def get_matured_investments():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM investment_user WHERE status = 'active' AND maturity_date <= CURDATE()"
        )
        return cursor.fetchall()


def complete_investment(investment_id, user_id, payout_amount):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE investment_user SET status = 'completed' WHERE id = %s",
            (investment_id,)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance + %s WHERE user_id = %s",
            (payout_amount, user_id)
        )
    db.commit()
