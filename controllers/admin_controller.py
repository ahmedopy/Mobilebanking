"""
controllers/admin_controller.py
Handles: admin approvals, admin reports, user suspend, admin profile.
"""
from flask import Blueprint, request, redirect, render_template, flash
from models import admin_model, user_model
from controllers.auth_controller import get_user_id_from_cookie

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/approvals', methods=['GET', 'POST'])
def approvals():
    if request.method == 'GET':
        pending = admin_model.get_approval_requests()
        return render_template('admin_approvals.html', pending=pending)

    phone = request.form.get('phone')
    action = request.form.get('action')

    if action == 'authorize':
        admin_model.update_admin_status(phone, 'authorized')
        flash('Admin authorized.', 'success')
    elif action == 'deny':
        admin_model.update_admin_status(phone, 'denied')
        flash('Admin denied.', 'info')

    return redirect('/approvals')


@admin_bp.route('/admin_reports')
def admin_reports():
    reports = admin_model.get_all_admin_reports()
    return render_template('admin_reports.html', reports=reports)


@admin_bp.route('/user_suspend', methods=['GET', 'POST'])
def user_suspend():
    users = []
    selected_user = None
    search_query = ''

    if request.method == 'POST':
        form_data = request.form
        search_query = form_data.get('search_query') or form_data.get('selected_phone')

        if search_query:
            users = user_model.search_users(search_query)
            if users:
                selected_user = users[0]
                suspend_key = f"status_{selected_user['phone_number']}"
                if suspend_key in form_data:
                    new_status = form_data[suspend_key]
                    if new_status:
                        user_model.update_user_status(selected_user['phone_number'], new_status)
                        # Refresh
                        refreshed = user_model.get_user_by_phone(selected_user['phone_number'])
                        if refreshed:
                            selected_user = refreshed

    return render_template('user_suspend.html',
                           users=users,
                           selected_user=selected_user,
                           search_query=search_query)


@admin_bp.route('/admin_profile')
def admin_profile():
    return render_template('admin_profile.html')
