"""
models/transaction_model.py
All database queries related to money transfers, scheduled transactions,
bank, card, send_now, and history.
"""
import random
import string
from models.database import get_db


def generate_unique_trx_id():
    db = get_db()
    with db.cursor() as cursor:
        while True:
            trx_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            cursor.execute("SELECT trx_id FROM send_money WHERE trx_id = %s", (trx_id,))
            if not cursor.fetchone():
                return trx_id


def get_history(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM send_money WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()


def get_pending_installments(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM pending_installments WHERE user_id = %s", (user_id,))
        return cursor.fetchall()


def get_scheduled_transactions(user_id=None):
    db = get_db()
    with db.cursor() as cursor:
        if user_id:
            cursor.execute(
                "SELECT * FROM scheduled_transactions WHERE user_id = %s AND status = 'pending'",
                (user_id,)
            )
        else:
            cursor.execute("SELECT * FROM scheduled_transactions WHERE status = 'pending'")
        return cursor.fetchall()


def insert_scheduled_transaction(user_id, recipient_phone, amount, schedule_date, trx_type):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """INSERT INTO scheduled_transactions
               (user_id, recipient_phone, amount, schedule_date, trx_type, status)
               VALUES (%s, %s, %s, %s, %s, 'pending')""",
            (user_id, recipient_phone, amount, schedule_date, trx_type)
        )
    db.commit()


def update_scheduled_transaction_status(trx_id, status):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "UPDATE scheduled_transactions SET status = %s WHERE id = %s",
            (status, trx_id)
        )
    db.commit()


def get_bank_accounts(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM bank_accounts WHERE user_id = %s", (user_id,))
        return cursor.fetchall()


def add_money_bank(user_id, amount, trx_id, bank_name, account_number):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO add_money_bank (user_id, amount, trx_id, bank_name, account_number) VALUES (%s, %s, %s, %s, %s)",
            (user_id, amount, trx_id, bank_name, account_number)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance + %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()


def get_card_info(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM cards WHERE user_id = %s", (user_id,))
        return cursor.fetchone()


def add_money_card(user_id, amount, trx_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO add_money_card (user_id, amount, trx_id) VALUES (%s, %s, %s)",
            (user_id, amount, trx_id)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance + %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()


def get_send_money_confirmation(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM send_money WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        return cursor.fetchone()


def insert_send_money(user_id, recipient_id, amount, trx_id, note=None):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO send_money (user_id, recipient_id, amount, trx_id, note) VALUES (%s, %s, %s, %s, %s)",
            (user_id, recipient_id, amount, trx_id, note)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
            (amount, user_id)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance + %s WHERE user_id = %s",
            (amount, recipient_id)
        )
    db.commit()


def insert_international_transfer(user_id, recipient_phone, amount_bdt, currency, trx_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """INSERT INTO send_money_international
               (user_id, recipient_phone, amount_in_bdt, currency, trx_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, recipient_phone, amount_bdt, currency, trx_id)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
            (amount_bdt, user_id)
        )
    db.commit()


def cancel_transaction(trx_id, user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM send_money WHERE trx_id = %s AND user_id = %s",
            (trx_id, user_id)
        )
        trx = cursor.fetchone()
        if trx:
            cursor.execute("DELETE FROM send_money WHERE trx_id = %s", (trx_id,))
            cursor.execute(
                "UPDATE user_profile SET balance = balance + %s WHERE user_id = %s",
                (trx['amount'], user_id)
            )
            cursor.execute(
                "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
                (trx['amount'], trx['recipient_id'])
            )
    db.commit()
    return trx if trx else None


def get_all_transactions(user_id):
    """Returns all transaction types for statement PDF generation."""
    db = get_db()
    result = {}
    queries = {
        'add_money_bank': "SELECT trx_id, amount FROM add_money_bank WHERE user_id=%s",
        'add_money_card': "SELECT trx_id, amount FROM add_money_card WHERE user_id=%s",
        'send_money': "SELECT trx_id, amount FROM send_money WHERE user_id=%s",
        'send_money_international': "SELECT trx_id, amount_in_bdt FROM send_money_international WHERE user_id=%s",
        'loans': "SELECT trx_id, loan_amount FROM loans WHERE user_id=%s",
        'investments': "SELECT trx_id, amount FROM investment_user WHERE user_id=%s",
        'electricity': "SELECT meter_no, amount FROM pay_electricity WHERE user_id=%s",
        'gas': "SELECT meter_no, amount FROM pay_gas WHERE user_id=%s",
        'wifi': "SELECT wifi_id, amount FROM pay_wifi WHERE user_id=%s",
    }
    with db.cursor() as cursor:
        for key, sql in queries.items():
            cursor.execute(sql, (user_id,))
            result[key] = cursor.fetchall()
    return result
