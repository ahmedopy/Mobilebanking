"""
controllers/messaging_controller.py  — FIXED
All variable names match templates exactly.
"""
from flask import Blueprint, request, redirect, render_template, jsonify
from models.database import get_db
from controllers.auth_controller import get_user_id_from_cookie
import traceback

messaging_bp = Blueprint('messaging', __name__)

# ── Notifications ──────────────────────────────────────────────────────────────
@messaging_bp.route('/notifications')
def notifications():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT alerts, timestamp FROM notifications WHERE user_id=%s ORDER BY id DESC", (user_id,))
        # template: for note in notifications  — note.alerts, note.timestamp
        notifications_list = cursor.fetchall()
    return render_template('notifications.html', notifications=notifications_list)

@messaging_bp.route('/clear_notifications', methods=['POST'])
def clear_notifications():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM notifications WHERE user_id=%s", (user_id,))
    db.commit()
    return redirect('/notifications')

# ── User Messages ──────────────────────────────────────────────────────────────
@messaging_bp.route('/user_messages', methods=['GET', 'POST'])
def user_messages():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    try:
        if request.method == 'POST':
            message = request.form.get('message', '').strip()
            if message:
                with db.cursor() as cursor:
                    cursor.execute("INSERT INTO messages (sender_id,message,role) VALUES (%s,%s,'user')",
                                   (user_id, message))
                    db.commit()
                return redirect('/user_messages')

        with db.cursor() as cursor:
            # template: for msg in messages — msg.message, msg.timestamp
            cursor.execute("""
                SELECT message, role, timestamp FROM messages
                WHERE (sender_id=%s AND role='user') OR (recipient_id=%s AND role='admin')
                ORDER BY timestamp ASC
            """, (user_id, user_id))
            messages = cursor.fetchall()
    except Exception:
        messages = []
    return render_template('user_messages.html', messages=messages)

# ── Admin Inbox ────────────────────────────────────────────────────────────────
@messaging_bp.route('/admin_inbox')
def admin_inbox():
    admin_id = request.cookies.get('admin_id')
    if not admin_id:
        return redirect('/admin_login')
    db = get_db()
    try:
        with db.cursor() as cursor:
            # template: for convo in conversations — convo.user_id, convo.phone_number, convo.message
            cursor.execute("""
                SELECT m1.sender_id AS user_id,
                       u.phone_number,
                       m1.message,
                       m1.timestamp
                FROM messages m1
                JOIN user_profile u ON m1.sender_id=u.user_id
                WHERE m1.role='user'
                AND m1.timestamp=(
                    SELECT MAX(m2.timestamp) FROM messages m2
                    WHERE m2.sender_id=m1.sender_id AND m2.role='user'
                )
                ORDER BY m1.timestamp DESC
            """)
            conversations = cursor.fetchall()
    except Exception:
        traceback.print_exc()
        conversations = []
    return render_template('admin_inbox.html', conversations=conversations)

# ── Admin Messages ─────────────────────────────────────────────────────────────
@messaging_bp.route('/admin_messages/<int:user_id>', methods=['GET', 'POST'])
def admin_messages(user_id):
    admin_id = request.cookies.get('admin_id')
    if not admin_id:
        return redirect('/admin_login')
    db = get_db()
    try:
        if request.method == 'POST':
            msg = request.form.get('message', '').strip()
            if msg:
                with db.cursor() as cursor:
                    cursor.execute("INSERT INTO messages (sender_id,recipient_id,message,role) VALUES (NULL,%s,%s,'admin')",
                                   (user_id, msg))
                    db.commit()
            return redirect(f'/admin_messages/{user_id}')

        with db.cursor() as cursor:
            cursor.execute("UPDATE messages SET is_read=TRUE WHERE sender_id=%s AND role='user' AND is_read=FALSE", (user_id,))
            db.commit()
            # template: for msg in messages — msg.message, msg.timestamp  AND  user_id
            cursor.execute("""
                SELECT message, role, timestamp FROM messages
                WHERE (sender_id=%s AND role='user') OR (recipient_id=%s AND role='admin')
                ORDER BY timestamp ASC
            """, (user_id, user_id))
            messages = cursor.fetchall()
        return render_template('admin_messages.html', messages=messages, user_id=user_id)
    except Exception:
        traceback.print_exc()
        return "Internal Server Error", 500

# ── Request Money ──────────────────────────────────────────────────────────────
@messaging_bp.route('/request_money', methods=['GET', 'POST'])
def request_money():
    if request.method == 'GET':
        return render_template('request_money.html')
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    phone  = request.form.get('phone')
    amount = request.form.get('amount')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT phone_number FROM user_profile WHERE user_id=%s", (user_id,))
        current_user = cursor.fetchone()
        cursor.execute("SELECT user_id FROM user_profile WHERE phone_number=%s", (phone,))
        receiver = cursor.fetchone()
    if not receiver:
        return redirect('/request_money?status=not_found')
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                       (receiver['user_id'], f"{current_user['phone_number']} requested {amount} Taka"))
        db.commit()
    return redirect('/request_money?status=success')

# ── Gift Card  (uses Jinja vars success/error NOT flash) ──────────────────────
@messaging_bp.route('/gift_card', methods=['GET', 'POST'])
def gift_card():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    if request.method == 'GET':
        # template: {% if success %} / {% if error %} as direct vars
        return render_template('gift_card.html')
    card_code = request.form.get('giftcode', '').strip().upper()
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT amount FROM gift_cards WHERE card_no=%s AND status='active'", (card_code,))
            card = cursor.fetchone()
            if not card:
                return render_template('gift_card.html', error="Invalid redeem code")
            amount = card['amount']
            cursor.execute("UPDATE user_profile SET balance=balance+%s WHERE user_id=%s", (amount, user_id))
            cursor.execute("UPDATE gift_cards SET status='used' WHERE card_no=%s", (card_code,))
            cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                           (user_id, f"Gift card of {amount} Taka Redeemed!"))
            db.commit()
        return render_template('gift_card.html', success="Code Redeemed!!!")
    except Exception:
        db.rollback()
        return render_template('gift_card.html', error="An error occurred during redemption.")

# ── Loyalty Points ─────────────────────────────────────────────────────────────
@messaging_bp.route('/loyalty_points')
def loyalty_points_page():
    return render_template('loyalty_points.html')

@messaging_bp.route('/api/loyalty_points')
def get_loyalty_points():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify(None)
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT points, tier FROM user_profile WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()
    return jsonify(row)

@messaging_bp.route('/api/update-loyalty-points', methods=['POST'])
def update_loyalty_points():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    data      = request.get_json() or {}
    add_pts   = int(data.get('points', 0))
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT points FROM user_profile WHERE user_id=%s", (user_id,))
            row = cursor.fetchone()
            new_points = (row['points'] or 0) + add_pts
            tiers = [
                ("Bronze", 0, 99), ("Silver", 100, 299),
                ("Gold", 300, 699), ("Platinum", 700, 1199), ("Diamond", 1200, float('inf'))
            ]
            new_tier = "Bronze"
            for name, lo, hi in tiers:
                if lo <= new_points <= hi:
                    new_tier = name
            cursor.execute("UPDATE user_profile SET points=%s, tier=%s WHERE user_id=%s",
                           (new_points, new_tier, user_id))
            db.commit()
        return jsonify({'success': True, 'new_points': new_points, 'new_tier': new_tier})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
