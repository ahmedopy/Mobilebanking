"""
controllers/utility_controller.py
Handles: gas bill, electricity bill, wifi bill payments.
"""
from flask import Blueprint, request, redirect, render_template, flash
from models import utility_model
from controllers.auth_controller import get_user_id_from_cookie

utility_bp = Blueprint('utility', __name__)


@utility_bp.route('/gas_bill', methods=['GET', 'POST'])
def gas_bill():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        bills = utility_model.get_gas_bills(user_id)
        return render_template('gas_bill.html', bills=bills)

    meter_no = request.form.get('meter_no')
    amount = request.form.get('amount')
    company = request.form.get('company', '')
    try:
        utility_model.pay_gas_bill(user_id, meter_no, amount, company)
        flash('Gas bill paid successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/gas_bill')


@utility_bp.route('/electricity_bill', methods=['GET', 'POST'])
def electricity_bill():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        bills = utility_model.get_electricity_bills(user_id)
        return render_template('electricity_bill.html', bills=bills)

    meter_no = request.form.get('meter_no')
    amount = request.form.get('amount')
    company = request.form.get('company', '')
    try:
        utility_model.pay_electricity_bill(user_id, meter_no, amount, company)
        flash('Electricity bill paid successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/electricity_bill')


@utility_bp.route('/wifi_bill', methods=['GET', 'POST'])
def wifi_bill():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        bills = utility_model.get_wifi_bills(user_id)
        return render_template('wifi_bill.html', bills=bills)

    wifi_id = request.form.get('wifi_id')
    amount = request.form.get('amount')
    provider = request.form.get('provider', '')
    try:
        utility_model.pay_wifi_bill(user_id, wifi_id, amount, provider)
        flash('Wi-Fi bill paid successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/wifi_bill')
