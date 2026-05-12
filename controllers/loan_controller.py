"""
controllers/loan_controller.py
Handles: loan request, approve loans (admin), active loans, pay loan.
"""
from flask import Blueprint, request, redirect, render_template, jsonify, flash
from models import loan_model, user_model
from controllers.auth_controller import get_user_id_from_cookie
import random
import string

loan_bp = Blueprint('loan', __name__)


def _generate_trx_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


@loan_bp.route('/api/request-loan', methods=['POST'])
def request_loan():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.get_json()
    amount = data.get('amount')
    duration = data.get('duration_months', 12)
    purpose = data.get('purpose', '')

    trx_id = _generate_trx_id()
    try:
        loan_model.insert_loan_request(user_id, amount, trx_id, duration, purpose)
        return jsonify({'success': True, 'trx_id': trx_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@loan_bp.route('/approve_loans', methods=['GET', 'POST'])
def approve_loans():
    if request.method == 'GET':
        loans = loan_model.get_pending_loans()
        return render_template('approve_loans.html', loans=loans)

    trx_id = request.form.get('trx_id')
    action = request.form.get('action')
    user_id = request.form.get('user_id')
    amount = request.form.get('amount')

    if action == 'approve':
        loan_model.approve_loan(trx_id, user_id, amount)
        flash('Loan approved.', 'success')
    elif action == 'deny':
        loan_model.deny_loan(trx_id)
        flash('Loan denied.', 'info')

    return redirect('/approve_loans')


@loan_bp.route('/active_loans')
def active_loans():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    loans = loan_model.get_active_loans(user_id)
    return render_template('active_loans.html', loans=loans)


@loan_bp.route('/pay_loan/<trx_id>', methods=['POST'])
def pay_loan(trx_id):
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    amount = request.form.get('amount')
    try:
        loan_model.pay_loan(trx_id, user_id, amount)
        flash('Loan payment successful.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/active_loans')
