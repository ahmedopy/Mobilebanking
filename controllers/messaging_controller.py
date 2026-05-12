"""
controllers/messaging_controller.py
Handles: user messages, admin inbox, admin messages, notifications,
gift cards, loyalty points.
"""
from flask import Blueprint, request, redirect, render_template, flash, jsonify
from models import messaging_model, user_model
from controllers.auth_controller import get_user_id_from_cookie

messaging_bp = Blueprint('messaging', __name__)


# ── Notifications ─────────────────────────────────────────────────────────────

@messaging_bp.route('/notifications')
def notifications():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    alerts = messaging_model.get_notifications(user_id)
    return render_template('notifications.html', alerts=alerts)


@messaging_bp.route('/clear_notifications', methods=['POST'])
def clear_notifications():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    messaging_model.clear_notifications(user_id)
    return redirect('/notifications')


# ── User Messages ──────────────────────────────────────────────────────────────

@messaging_bp.route('/user_messages', methods=['GET', 'POST'])
def user_messages():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        messages = messaging_model.get_user_messages(user_id)
        return render_template('user_messages.html', messages=messages)

    subject = request.form.get('subject', '')
    body = request.form.get('body', '')
    messaging_model.send_user_message(user_id, subject, body)
    flash('Message sent.', 'success')
    return redirect('/user_messages')


# ── Admin Inbox ────────────────────────────────────────────────────────────────

@messaging_bp.route('/admin_inbox')
def admin_inbox():
    admin_id = request.cookies.get('admin_id')
    if not admin_id:
        return redirect('/admin_login')
    messages = messaging_model.get_all_messages()
    return render_template('admin_inbox.html', messages=messages)


@messaging_bp.route('/admin_messages/<int:user_id>', methods=['GET', 'POST'])
def admin_messages(user_id):
    admin_id = request.cookies.get('admin_id')
    if not admin_id:
        return redirect('/admin_login')

    if request.method == 'GET':
        messages = messaging_model.get_messages_by_user(user_id)
        return render_template('admin_messages.html', messages=messages, target_user_id=user_id)

    body = request.form.get('body', '')
    messaging_model.send_admin_reply(user_id, body)
    flash('Reply sent.', 'success')
    return redirect(f'/admin_messages/{user_id}')


# ── Request Money ──────────────────────────────────────────────────────────────

@messaging_bp.route('/request_money', methods=['GET', 'POST'])
def request_money():
    if request.method == 'GET':
        return render_template('request_money.html')

    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    phone = request.form.get('phone')
    amount = request.form.get('amount')

    current_user = user_model.get_user_by_id(user_id)
    if not current_user:
        return redirect('/login')

    receiver = user_model.get_user_by_phone(phone)
    if not receiver:
        return redirect('/request_money?status=not_found')

    message = f"{current_user['phone_number']} requested {amount} Taka"
    messaging_model.insert_notification(receiver['user_id'], message)
    return redirect('/request_money?status=success')


# ── Gift Card ──────────────────────────────────────────────────────────────────

@messaging_bp.route('/gift_card', methods=['GET', 'POST'])
def gift_card():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        return render_template('gift_card.html')

    code = request.form.get('code', '').strip()
    card = messaging_model.redeem_gift_card(user_id, code)
    if card:
        flash(f"Gift card redeemed! {card['amount']} BDT added.", 'success')
    else:
        flash('Invalid or already used gift card.', 'error')
    return redirect('/gift_card')


# ── Loyalty Points ─────────────────────────────────────────────────────────────

@messaging_bp.route('/api/loyalty_points')
def get_loyalty_points():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify(None)
    points = messaging_model.get_loyalty_points(user_id)
    return jsonify(points)


@messaging_bp.route('/loyalty_points', methods=['GET'])
def loyalty_points_page():
    return render_template('loyalty_points.html')


@messaging_bp.route('/loyalty_points', methods=['POST'])
def update_loyalty_points():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    points = request.form.get('points', 0)
    messaging_model.update_loyalty_points(user_id, points)
    flash('Loyalty points updated.', 'success')
    return redirect('/loyalty_points')
