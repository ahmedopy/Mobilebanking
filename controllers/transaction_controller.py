"""
controllers/transaction_controller.py  — FIXED
All variable names match templates exactly.
"""
from flask import (Blueprint, request, redirect, render_template,
                   flash, jsonify, send_file, url_for)
from models.database import get_db
from models import user_model
from controllers.auth_controller import get_user_id_from_cookie
import traceback, random, string
from datetime import datetime as dt, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas

transaction_bp = Blueprint('transaction', __name__)

EXCHANGE_RATES = {
    'Australia': 77.27, 'Canada': 85.05, 'China': 16.67,
    'France': 131.64, 'Germany': 131.64, 'Saudi Arabia': 32.39
}

def _generate_trx_id():
    db = get_db()
    with db.cursor() as cursor:
        while True:
            tid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            cursor.execute("SELECT trx_id FROM send_money WHERE trx_id=%s", (tid,))
            if not cursor.fetchone():
                return tid

# ── History ────────────────────────────────────────────────────────────────────
@transaction_bp.route('/history')
def history():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT type, trx_id, account, time, amount
                FROM history WHERE user_id=%s ORDER BY time DESC
            """, (user_id,))
            history_records = cursor.fetchall()
    except Exception:
        history_records = []
    # template uses: for record in history_records
    return render_template('history.html', history_records=history_records)

# ── Send Now ───────────────────────────────────────────────────────────────────
@transaction_bp.route('/send_now', methods=['GET', 'POST'])
def send_now():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return render_template('login.html')

    if request.method == 'GET':
        # template uses: prefill_name, prefill_phone, success
        prefill_name  = request.args.get('name', '')
        prefill_phone = request.args.get('phone', '')
        success       = request.args.get('success', '')
        return render_template('send_now.html',
                               prefill_name=prefill_name,
                               prefill_phone=prefill_phone,
                               success=success)

    recipient_phone = request.form.get('recipient_phone')
    recipient_name  = request.form.get('recipient_name')
    save_info       = request.form.get('save_info')
    try:
        amount = float(request.form.get('amount', 0))
        if amount <= 0:
            return redirect(url_for('transaction.send_now', success='0'))
    except (ValueError, TypeError):
        return redirect(url_for('transaction.send_now', success='0'))

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user_profile WHERE phone_number=%s", (recipient_phone,))
        recipient = cursor.fetchone()
        if not recipient:
            return redirect(url_for('transaction.send_now', success='0'))

        cursor.execute("SELECT balance, transaction_limit FROM user_profile WHERE user_id=%s", (user_id,))
        sender = cursor.fetchone()
        if not sender:
            return render_template('login.html')

        if float(sender['balance']) < amount:
            return redirect(url_for('transaction.send_now', status='insufficient_balance'))
        if sender['transaction_limit'] and float(sender['transaction_limit']) < amount:
            return redirect(url_for('transaction.send_now', status='limit_reached'))

        trx_id = _generate_trx_id()
        cursor.execute("INSERT INTO send_money (user_id, phone_no, name, amount, trx_id) VALUES (%s,%s,%s,%s,%s)",
                       (user_id, recipient_phone, recipient_name, amount, trx_id))
        cursor.execute("UPDATE user_profile SET balance=balance-%s WHERE user_id=%s", (amount, user_id))
        cursor.execute("UPDATE user_profile SET balance=balance+%s WHERE phone_number=%s", (amount, recipient_phone))

        if save_info == 'on':
            cursor.execute("INSERT IGNORE INTO saved_details (user_id,name,phone) VALUES (%s,%s,%s)",
                           (user_id, recipient_name, recipient_phone))

        cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                       (user_id, f"Sent {amount} to {recipient_name or recipient_phone}"))
        cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                       (recipient['user_id'], f"Received {amount} from User {user_id}"))
        cursor.execute("INSERT INTO history (user_id,type,trx_id,account,amount) VALUES (%s,%s,%s,%s,%s)",
                       (user_id, 'Send Money', trx_id, recipient_phone, -amount))
        db.commit()

    return redirect(url_for('transaction.send_now', status='success'))

# ── International ──────────────────────────────────────────────────────────────
@transaction_bp.route('/int_money_confirm_transaction')
def int_money_confirm_transaction():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM temporary_send_money_international WHERE user_id=%s", (user_id,))
            trx = cursor.fetchone()
        if not trx:
            return redirect('/send_money_int')
        amount_in_bdt = float(trx['amount'])
        country       = trx['country']
        rate          = EXCHANGE_RATES.get(country, 1)
        amount_in_selected_country = round(amount_in_bdt / rate, 2)
        # template uses all 7 vars as direct context
        return render_template('int_money_confirm.html',
                               account_no=trx['account_no'],
                               receivers_name=trx['receivers_name'],
                               country=country,
                               amount_in_bdt=amount_in_bdt,
                               amount_in_selected_country=amount_in_selected_country,
                               user_id=user_id,
                               trx_id=trx['trx_id'])
    except Exception:
        traceback.print_exc()
        return redirect('/send_money_int')

@transaction_bp.route('/confirm_international', methods=['POST'])
def confirm_international():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    try:
        trx_id      = request.form.get('trx_id')
        amount_bdt  = float(request.form.get('amount_in_bdt', 0))
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM temporary_send_money_international WHERE trx_id=%s AND user_id=%s",
                           (trx_id, user_id))
            trx = cursor.fetchone()
            if not trx:
                return redirect('/send_money_int')
            cursor.execute("""
                INSERT INTO send_money_international
                (trx_id,account_no,receivers_name,amount_in_bdt,amount_in_selected_country,country,user_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (trx['trx_id'], trx['account_no'], trx['receivers_name'],
                  amount_bdt, 0, trx['country'], user_id))
            cursor.execute("UPDATE user_profile SET balance=balance-%s WHERE user_id=%s", (amount_bdt, user_id))
            cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                           (user_id, f"International transfer of {amount_bdt} BDT to {trx['receivers_name']}"))
            cursor.execute("INSERT INTO history (user_id,type,trx_id,account,amount) VALUES (%s,%s,%s,%s,%s)",
                           (user_id, 'International Transfer', trx_id, trx['account_no'], -amount_bdt))
            cursor.execute("DELETE FROM temporary_send_money_international WHERE trx_id=%s", (trx_id,))
            db.commit()
        flash('International transfer successful!', 'success')
        return redirect('/home')
    except Exception as e:
        traceback.print_exc()
        flash(f'Error: {str(e)}', 'error')
        return redirect('/send_money_int')

# ── Add Money Bank ─────────────────────────────────────────────────────────────
@transaction_bp.route('/bank', methods=['GET', 'POST'])
def bank():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return render_template('login.html')
    if request.method == 'GET':
        return render_template('bank.html')
    acc_no = request.form.get('acc_no', '')
    try:
        amount = float(request.form.get('amount', 0))
        trx_id = _generate_trx_id()
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO add_money_bank (user_id,acc_no,amount,trx_id) VALUES (%s,%s,%s,%s)",
                           (user_id, acc_no, amount, trx_id))
            cursor.execute("UPDATE user_profile SET balance=balance+%s WHERE user_id=%s", (amount, user_id))
            cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                           (user_id, f"Added {amount} BDT from bank account"))
            cursor.execute("INSERT INTO history (user_id,type,trx_id,account,amount) VALUES (%s,%s,%s,%s,%s)",
                           (user_id, 'Add Money (Bank)', trx_id, acc_no, amount))
            db.commit()
        flash('Money added from bank!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/home')

# ── Add Money Card ─────────────────────────────────────────────────────────────
@transaction_bp.route('/card', methods=['GET', 'POST'])
def card():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return render_template('login.html')
    if request.method == 'GET':
        return render_template('card.html')
    card_no = request.form.get('card_no', '')
    try:
        amount = float(request.form.get('amount', 0))
        trx_id = _generate_trx_id()
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO add_money_card (user_id,card_no,amount,trx_id) VALUES (%s,%s,%s,%s)",
                           (user_id, card_no, amount, trx_id))
            cursor.execute("UPDATE user_profile SET balance=balance+%s WHERE user_id=%s", (amount, user_id))
            cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                           (user_id, f"Added {amount} BDT from card"))
            cursor.execute("INSERT INTO history (user_id,type,trx_id,account,amount) VALUES (%s,%s,%s,%s,%s)",
                           (user_id, 'Add Money (Card)', trx_id, card_no, amount))
            db.commit()
        flash('Money added from card!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/home')

# ── Cancel Transaction (report to admin) ──────────────────────────────────────
@transaction_bp.route('/cancel_transaction/<trx_id>', methods=['POST'])
def cancel_transaction(trx_id):
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    try:
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT amount FROM history WHERE LOWER(trx_id)=LOWER(%s) AND user_id=%s",
                           (trx_id, user_id))
            result = cursor.fetchone()
            if not result:
                return jsonify({"status": "error", "message": "Transaction not found"})
            cursor.execute("SELECT * FROM admin_reports WHERE user_id=%s AND trx_id=%s AND report_type='Request Cancellation'",
                           (user_id, trx_id))
            if cursor.fetchone():
                return jsonify({"status": "exists", "message": "Already requested"})
            cursor.execute("INSERT INTO admin_reports (user_id,report_type,trx_id,amount) VALUES (%s,'Request Cancellation',%s,%s)",
                           (user_id, trx_id, result['amount']))
            db.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ── Schedule Transactions ──────────────────────────────────────────────────────
@transaction_bp.route('/schedule_transactions', methods=['GET', 'POST'])
def schedule_transactions():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    current_time = dt.now().strftime('%Y-%m-%dT%H:%M')

    if request.method == 'GET':
        # template uses: current_time, error, success
        return render_template('schedule_transactions.html', current_time=current_time)

    phone              = request.form.get('account')
    amount_str         = request.form.get('amount')
    scheduled_time_str = request.form.get('datetime')
    try:
        amount         = float(amount_str)
        if amount <= 0:
            raise ValueError("Invalid amount")
        scheduled_time = dt.strptime(scheduled_time_str, "%Y-%m-%dT%H:%M")
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT user_id FROM user_profile WHERE phone_number=%s", (phone,))
            receiver = cursor.fetchone()
            if not receiver:
                return render_template('schedule_transactions.html',
                                       error="Recipient not found.", current_time=current_time)
            cursor.execute("INSERT INTO schedule_transactions (sender_id,receiver_id,amount,scheduled_time) VALUES (%s,%s,%s,%s)",
                           (user_id, receiver['user_id'], amount, scheduled_time))
            db.commit()
        return render_template('schedule_transactions.html',
                               success="Transaction scheduled successfully!", current_time=current_time)
    except Exception:
        return render_template('schedule_transactions.html',
                               error="Failed to schedule transaction.", current_time=current_time)

@transaction_bp.route('/api/pending-scheduled-transactions')
def get_pending_scheduled():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify([])
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT sp.scheduled_time, sp.amount, up.phone_number AS receiver_phone
            FROM schedule_transactions sp
            JOIN user_profile up ON sp.receiver_id=up.user_id
            WHERE sp.sender_id=%s AND sp.status='pending'
        """, (user_id,))
        rows = cursor.fetchall()
    return jsonify([{'scheduled_time': str(r['scheduled_time']),
                     'amount': float(r['amount']),
                     'receiver_phone': r['receiver_phone']} for r in rows])

# ── Download Statement ─────────────────────────────────────────────────────────
@transaction_bp.route('/download_statements')
def download_statements():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT first_name,last_name,email,phone_number FROM user_profile WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()

    buffer = BytesIO()
    pdf    = pdf_canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    try:
        pdf.drawImage("templates/logo.png", 40, y-50, width=100, height=80)
    except Exception:
        pass
    y -= 70
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(200, y, "Transaction Statement")
    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Name: {user['first_name']} {user['last_name']}")
    y -= 15; pdf.drawString(40, y, f"Email: {user['email']}")
    y -= 15; pdf.drawString(40, y, f"Phone: {user['phone_number']}")
    y -= 15; pdf.drawString(40, y, f"Generated: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30

    sections = [
        ("Add Money (Bank)",    "SELECT trx_id,amount FROM add_money_bank WHERE user_id=%s",                ['trx_id','amount']),
        ("Add Money (Card)",    "SELECT trx_id,amount FROM add_money_card WHERE user_id=%s",                ['trx_id','amount']),
        ("Sent Money",          "SELECT trx_id,amount FROM send_money WHERE user_id=%s",                    ['trx_id','amount']),
        ("Sent International",  "SELECT trx_id,amount_in_bdt FROM send_money_international WHERE user_id=%s",['trx_id','amount_in_bdt']),
        ("Loans",               "SELECT trx_id,loan_amount FROM loans WHERE user_id=%s",                    ['trx_id','loan_amount']),
        ("Investments",         "SELECT trx_id,amount FROM investment_user WHERE user_id=%s",               ['trx_id','amount']),
        ("Electricity Bills",   "SELECT meter_no,amount FROM pay_electricity WHERE user_id=%s",             ['meter_no','amount']),
        ("Gas Bills",           "SELECT meter_no,amount FROM pay_gas WHERE user_id=%s",                     ['meter_no','amount']),
        ("Wi-Fi Bills",         "SELECT wifi_id,amount FROM pay_wifi WHERE user_id=%s",                     ['wifi_id','amount']),
    ]
    with db.cursor() as cursor:
        for title, sql, headers in sections:
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            if not rows:
                continue
            if y < 100:
                pdf.showPage(); y = height - 50
            pdf.setFont("Helvetica-Bold", 12); pdf.drawString(40, y, title); y -= 20
            pdf.setFont("Helvetica-Bold", 10)
            for i, h in enumerate(headers):
                pdf.drawString(40+i*150, y, h.replace('_',' ').title())
            y -= 15
            pdf.setFont("Helvetica", 10)
            for row in rows:
                for i, key in enumerate(headers):
                    pdf.drawString(40+i*150, y, str(row.get(key, '')))
                y -= 15
                if y < 100:
                    pdf.showPage(); y = height - 50
            y -= 10
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="statement.pdf", mimetype='application/pdf')
