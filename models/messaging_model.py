"""
models/messaging_model.py
Database queries for user messages, admin inbox, notifications, and gift cards.
"""
from models.database import get_db


# ── Notifications ─────────────────────────────────────────────────────────────

def get_notifications(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY id DESC",
            (user_id,)
        )
        return cursor.fetchall()


def clear_notifications(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
    db.commit()


def insert_notification(user_id, message):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO notifications (user_id, alerts) VALUES (%s, %s)",
            (user_id, message)
        )
    db.commit()


# ── User Messages ──────────────────────────────────────────────────────────────

def get_user_messages(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM messages WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        return cursor.fetchall()


def send_user_message(user_id, subject, body):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO messages (user_id, subject, body) VALUES (%s, %s, %s)",
            (user_id, subject, body)
        )
    db.commit()


# ── Admin Inbox ────────────────────────────────────────────────────────────────

def get_all_messages():
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM messages ORDER BY created_at DESC")
        return cursor.fetchall()


def get_messages_by_user(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM messages WHERE user_id = %s ORDER BY created_at",
            (user_id,)
        )
        return cursor.fetchall()


def send_admin_reply(user_id, body):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO messages (user_id, subject, body, sender) VALUES (%s, 'Admin Reply', %s, 'admin')",
            (user_id, body)
        )
    db.commit()


# ── Gift Cards ─────────────────────────────────────────────────────────────────

def redeem_gift_card(user_id, code):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM gift_cards WHERE code = %s AND status = 'active'",
            (code,)
        )
        card = cursor.fetchone()
        if card:
            cursor.execute(
                "UPDATE gift_cards SET status = 'used', used_by = %s WHERE code = %s",
                (user_id, code)
            )
            cursor.execute(
                "UPDATE user_profile SET balance = balance + %s WHERE user_id = %s",
                (card['amount'], user_id)
            )
            db.commit()
        return card


# ── Loyalty Points ─────────────────────────────────────────────────────────────

def get_loyalty_points(user_id):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM loyalty_points WHERE user_id = %s",
            (user_id,)
        )
        return cursor.fetchone()


def update_loyalty_points(user_id, points):
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM loyalty_points WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                "UPDATE loyalty_points SET points = points + %s WHERE user_id = %s",
                (points, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO loyalty_points (user_id, points) VALUES (%s, %s)",
                (user_id, points)
            )
    db.commit()
