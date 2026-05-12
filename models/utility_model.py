"""
models/utility_model.py
All database queries related to utility bill payments
(gas, electricity, wifi).
"""
from models.database import get_db


def pay_gas_bill(user_id, meter_no, amount, company):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO pay_gas (user_id, meter_no, amount, company) VALUES (%s, %s, %s, %s)",
            (user_id, meter_no, amount, company)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()


def pay_electricity_bill(user_id, meter_no, amount, company):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO pay_electricity (user_id, meter_no, amount, company) VALUES (%s, %s, %s, %s)",
            (user_id, meter_no, amount, company)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()


def pay_wifi_bill(user_id, wifi_id, amount, provider):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO pay_wifi (user_id, wifi_id, amount, provider) VALUES (%s, %s, %s, %s)",
            (user_id, wifi_id, amount, provider)
        )
        cursor.execute(
            "UPDATE user_profile SET balance = balance - %s WHERE user_id = %s",
            (amount, user_id)
        )
    db.commit()


def get_gas_bills(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM pay_gas WHERE user_id = %s ORDER BY id DESC", (user_id,))
        return cursor.fetchall()


def get_electricity_bills(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM pay_electricity WHERE user_id = %s ORDER BY id DESC", (user_id,))
        return cursor.fetchall()


def get_wifi_bills(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM pay_wifi WHERE user_id = %s ORDER BY id DESC", (user_id,))
        return cursor.fetchall()
