"""
controllers/investment_controller.py
Handles: invest page, investment options API, submit/confirm investment,
current investments.
"""
from flask import Blueprint, request, redirect, render_template, jsonify, flash
from models import investment_model, user_model
from controllers.auth_controller import get_user_id_from_cookie
import random
import string
from datetime import date
from dateutil.relativedelta import relativedelta

investment_bp = Blueprint('investment', __name__)


def _generate_trx_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


@investment_bp.route('/invest')
def invest_page():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    return render_template('investments.html')


@investment_bp.route('/api/get-investment-options')
def get_investment_options():
    options = investment_model.get_investment_options()
    return jsonify(options)


@investment_bp.route('/api/submit-investment', methods=['POST'])
def submit_investment():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.get_json()
    option_id = data.get('option_id')
    amount = data.get('amount')

    options = investment_model.get_investment_options()
    option = next((o for o in options if str(o['id']) == str(option_id)), None)
    if not option:
        return jsonify({'success': False, 'message': 'Invalid option'})

    user = user_model.get_user_by_id(user_id)
    if float(user['balance']) < float(amount):
        return jsonify({'success': False, 'message': 'Insufficient balance'})

    trx_id = _generate_trx_id()
    maturity_date = date.today() + relativedelta(months=int(option.get('duration_months', 6)))
    investment_model.insert_investment(user_id, option_id, amount, trx_id, maturity_date)
    return jsonify({'success': True, 'trx_id': trx_id})


@investment_bp.route('/api/get-latest-investment')
def get_latest_investment():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify(None)
    inv = investment_model.get_latest_investment(user_id)
    return jsonify(inv)


@investment_bp.route('/api/confirm-investment', methods=['POST'])
def confirm_investment():
    # Confirmation is handled via submit; this route returns status
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify({'success': False}), 401
    return jsonify({'success': True})


@investment_bp.route('/current_investments')
def current_investments():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    investments = investment_model.get_current_investments(user_id)
    return render_template('current_investments.html', investments=investments)
