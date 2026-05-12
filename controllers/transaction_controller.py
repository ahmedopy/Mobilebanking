"""
controllers/transaction_controller.py
Handles: send money (local & international), add money (bank/card),
send_now, cancel transaction, history, scheduled transactions,
download statements.
"""
from flask import (Blueprint, request, redirect, render_template,
                   flash, jsonify, send_file)
from models import transaction_model, user_model
from controllers.auth_controller import get_user_id_from_cookie
import threading
import traceback
import datetime
from datetime import datetime as dt, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas

transaction_bp = Blueprint('transaction', __name__)


# ── Send Money ─────────────────────────────────────────────────────────────────

@transaction_bp.route('/confirm_send_money', methods=['POST'])
def confirm_send_money():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    recipient_phone = request.form.get('phone')
    amount = request.form.get('amount')
    note = request.form.get('note', '')

    try:
        recipient = user_model.get_user_by_phone(recipient_phone)
        if not recipient:
            flash('Recipient not found.', 'error')
            return redirect('/send_money')

        trx_id = transaction_model.generate_unique_trx_id()
        transaction_model.insert_send_money(user_id, recipient['user_id'], amount, trx_id, note)
        flash(f'Money sent successfully! TRX ID: {trx_id}', 'success')
        return redirect('/home')
    except Exception as e:
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'error')
        return redirect('/send_money')


@transaction_bp.route('/submit_transaction', methods=['POST'])
def submit_transaction():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    trx_type = request.form.get('type')
    amount = request.form.get('amount')
    trx_id = transaction_model.generate_unique_trx_id()

    try:
        if trx_type == 'bank':
            bank_name = request.form.get('bank_name')
            account_number = request.form.get('account_number')
            transaction_model.add_money_bank(user_id, amount, trx_id, bank_name, account_number)
        elif trx_type == 'card':
            transaction_model.add_money_card(user_id, amount, trx_id)
        flash('Money added successfully!', 'success')
        return redirect('/home')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect('/add_money')


@transaction_bp.route('/int_money_confirm_transaction')
def int_money_confirm_transaction():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    return render_template('int_money_confirm.html')


@transaction_bp.route('/send_now', methods=['GET', 'POST'])
def send_now():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return render_template('login.html')

    if request.method == 'GET':
        return render_template('send_now.html')

    phone = request.form.get('phone')
    amount = request.form.get('amount')
    note = request.form.get('note', '')

    try:
        recipient = user_model.get_user_by_phone(phone)
        if not recipient:
            flash('Recipient not found.', 'error')
            return redirect('/send_now')

        trx_id = transaction_model.generate_unique_trx_id()
        transaction_model.insert_send_money(user_id, recipient['user_id'], amount, trx_id, note)
        flash(f'Sent! TRX ID: {trx_id}', 'success')
        return redirect('/home')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect('/send_now')


@transaction_bp.route('/cancel_transaction/<trx_id>', methods=['POST'])
def cancel_transaction(trx_id):
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    transaction_model.cancel_transaction(trx_id, user_id)
    flash('Transaction cancelled.', 'success')
    return redirect('/history')


@transaction_bp.route('/history')
def history():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    records = transaction_model.get_history(user_id)
    return render_template('history.html', records=records)


# ── Scheduled Transactions ─────────────────────────────────────────────────────

@transaction_bp.route('/schedule_transactions', methods=['GET', 'POST'])
def schedule_transactions():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        return render_template('schedule_transactions.html')

    recipient_phone = request.form.get('phone')
    amount = request.form.get('amount')
    schedule_date = request.form.get('schedule_date')
    trx_type = request.form.get('type', 'send_money')

    try:
        transaction_model.insert_scheduled_transaction(
            user_id, recipient_phone, amount, schedule_date, trx_type
        )
        flash('Transaction scheduled!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/scheduled_transactions')


@transaction_bp.route('/api/pending-scheduled-transactions')
def get_pending_scheduled():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify([])
    records = transaction_model.get_scheduled_transactions(user_id)
    return jsonify(records)


# ── Bank / Card ────────────────────────────────────────────────────────────────

@transaction_bp.route('/bank', methods=['GET', 'POST'])
def bank():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return render_template('login.html')

    if request.method == 'GET':
        accounts = transaction_model.get_bank_accounts(user_id)
        return render_template('bank.html', accounts=accounts)

    # POST: add money from bank
    amount = request.form.get('amount')
    bank_name = request.form.get('bank_name')
    account_number = request.form.get('account_number')
    trx_id = transaction_model.generate_unique_trx_id()
    try:
        transaction_model.add_money_bank(user_id, amount, trx_id, bank_name, account_number)
        flash('Money added from bank!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/home')


@transaction_bp.route('/card', methods=['GET', 'POST'])
def card():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return render_template('login.html')

    if request.method == 'GET':
        card_info = transaction_model.get_card_info(user_id)
        return render_template('card.html', card=card_info)

    amount = request.form.get('amount')
    trx_id = transaction_model.generate_unique_trx_id()
    try:
        transaction_model.add_money_card(user_id, amount, trx_id)
        flash('Money added from card!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/home')


# ── Download Statement ─────────────────────────────────────────────────────────

@transaction_bp.route('/download_statements')
def download_statements():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    user = user_model.get_user_by_id(user_id)
    all_trx = transaction_model.get_all_transactions(user_id)

    buffer = BytesIO()
    pdf = pdf_canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    logo_path = "templates/logo.png"
    try:
        pdf.drawImage(logo_path, 40, y - 50, width=100, height=80)
    except Exception:
        pass
    y -= 70

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(200, y, "Transaction Statement")
    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Name: {user['first_name']} {user['last_name']}")
    y -= 15
    pdf.drawString(40, y, f"Email: {user['email']}")
    y -= 15
    pdf.drawString(40, y, f"Phone: {user['phone_number']}")
    y -= 15
    pdf.drawString(40, y, f"Generated on: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30

    sections = [
        ("Added Money (Bank)",      all_trx['add_money_bank'],          ['Trx_id', 'Amount']),
        ("Added Money (Card)",      all_trx['add_money_card'],          ['Trx_id', 'Amount']),
        ("Sent Money",              all_trx['send_money'],              ['Trx_id', 'Amount']),
        ("Sent International",      all_trx['send_money_international'], ['Trx_id', 'Amount_in_bdt']),
        ("Loans",                   all_trx['loans'],                   ['Trx_id', 'Loan_amount']),
        ("Investments",             all_trx['investments'],             ['Trx_id', 'Amount']),
        ("Electricity Bills",       all_trx['electricity'],             ['Meter_no', 'Amount']),
        ("Gas Bills",               all_trx['gas'],                     ['Meter_no', 'Amount']),
        ("Wi-Fi Bills",             all_trx['wifi'],                    ['Wifi_id', 'Amount']),
    ]

    for title, records, headers in sections:
        if not records:
            continue
        if y < 100:
            pdf.showPage()
            y = height - 50
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, title)
        y -= 20
        pdf.setFont("Helvetica-Bold", 10)
        for i, header in enumerate(headers):
            pdf.drawString(40 + i * 100, y, header)
        y -= 15
        pdf.setFont("Helvetica", 10)
        for row in records:
            for i, key in enumerate(headers):
                pdf.drawString(40 + i * 100, y, str(row.get(key.lower(), '')))
            y -= 15
            if y < 100:
                pdf.showPage()
                y = height - 50
        y -= 10

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="statement.pdf", mimetype='application/pdf')
