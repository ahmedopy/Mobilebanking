"""
controllers/admin_controller.py  — FIXED
"""
from flask import Blueprint, request, redirect, render_template, flash
from models.database import get_db
from controllers.auth_controller import get_user_id_from_cookie
import traceback

admin_bp = Blueprint('admin', __name__)

# ── Approvals ──────────────────────────────────────────────────────────────────
@admin_bp.route('/approvals', methods=['GET', 'POST'])
def approvals():
    db = get_db()
    if request.method == 'GET':
        try:
            with db.cursor() as cursor:
                # template: for admin in pending_admins — status must be 'unauthorized'
                cursor.execute("""
                    SELECT first_name,last_name,email,nid,dob,phone_number
                    FROM admin_profile WHERE status='unauthorized'
                    ORDER BY admin_id ASC LIMIT 10
                """)
                pending_admins = cursor.fetchall()
        except Exception:
            pending_admins = []
        return render_template('admin_approvals.html', pending_admins=pending_admins)

    # POST
    phones  = request.form.getlist('phones')
    actions = request.form.getlist('actions')
    try:
        with db.cursor() as cursor:
            for phone, action in zip(phones, actions):
                if action == 'Approve':
                    cursor.execute("UPDATE admin_profile SET status='authorized' WHERE phone_number=%s", (phone,))
                elif action == 'Deny':
                    cursor.execute("UPDATE admin_profile SET status='denied' WHERE phone_number=%s", (phone,))
            db.commit()
        flash('Approvals updated.', 'success')
    except Exception:
        flash('Something went wrong.', 'error')
    return redirect('/approvals')

# ── Admin Reports ──────────────────────────────────────────────────────────────
@admin_bp.route('/admin_reports')
def admin_reports():
    db = get_db()
    with db.cursor() as cursor:
        # template: for req in cancel_requests — req.user_id, req.trx_id, req.report_type, req.amount
        cursor.execute("SELECT user_id, trx_id, report_type, amount FROM admin_reports ORDER BY id DESC")
        cancel_requests = cursor.fetchall()
    return render_template('admin_reports.html', cancel_requests=cancel_requests)

# ── User Suspend ───────────────────────────────────────────────────────────────
@admin_bp.route('/user_suspend', methods=['GET', 'POST'])
def user_suspend():
    # template: users, selected_user, search_query
    users         = []
    selected_user = None
    search_query  = ''

    if request.method == 'POST':
        search_query = request.form.get('search_query', '').strip()
        db = get_db()
        if search_query:
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, first_name, last_name, dob, email, phone_number,
                           nid, balance, transaction_limit, points, status
                    FROM user_profile
                    WHERE phone_number=%s OR first_name LIKE %s OR last_name LIKE %s OR nid=%s
                """, (search_query, f"%{search_query}%", f"%{search_query}%", search_query))
                users = cursor.fetchall()

            if users:
                selected_user = users[0]
                suspend_key   = f"status_{selected_user['phone_number']}"
                new_status    = request.form.get(suspend_key, '').strip()
                if new_status:
                    with db.cursor() as cursor:
                        cursor.execute("UPDATE user_profile SET status=%s WHERE phone_number=%s",
                                       (new_status, selected_user['phone_number']))
                        db.commit()
                    with db.cursor() as cursor:
                        cursor.execute("SELECT * FROM user_profile WHERE phone_number=%s",
                                       (selected_user['phone_number'],))
                        selected_user = cursor.fetchone()

    return render_template('user_suspend.html',
                           users=users,
                           selected_user=selected_user,
                           search_query=search_query)

# ── Admin Profile ──────────────────────────────────────────────────────────────
@admin_bp.route('/admin_profile')
def admin_profile():
    return render_template('admin_profile.html')
