"""
main_mvc.py  –  MVC entry-point
================================
This file wires together:
  • Flask app initialisation
  • All Blueprint controllers  (controllers/)
  • Background worker threads (unchanged from original app.py)

The ORIGINAL app.py is left completely untouched and still works
on its own.  Run this file instead to use the MVC layout.

Usage:
    python main_mvc.py
"""

import os
import threading
from flask import Flask, render_template, redirect, request
from controllers.auth_controller        import auth_bp
from controllers.profile_controller     import profile_bp
from controllers.transaction_controller import transaction_bp
from controllers.investment_controller  import investment_bp
from controllers.loan_controller        import loan_bp
from controllers.utility_controller     import utility_bp
from controllers.messaging_controller   import messaging_bp
from controllers.admin_controller       import admin_bp
from controllers.favourite_controller   import favourite_bp

# ── App factory ───────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder='views/templates', static_folder='views/static')
app.secret_key = 'your_secret_key_here'

# ── Register blueprints ───────────────────────────────────────────────────────

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(transaction_bp)
app.register_blueprint(investment_bp)
app.register_blueprint(loan_bp)
app.register_blueprint(utility_bp)
app.register_blueprint(messaging_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(favourite_bp)


# ── Simple page routes (view-only, no business logic) ─────────────────────────

@app.route('/')
def homepage():
    return render_template('landing.html')

@app.route('/home')
def home():
    from controllers.auth_controller import get_user_id_from_cookie
    from models.user_model import get_user_by_id
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    user = get_user_by_id(user_id)
    if user:
        return render_template('home.html', user=user)
    return "User not found", 404

@app.route('/admin_home')
def admin_home():
    return render_template('admin_home.html')

@app.route('/add_money')
def add_money():
    return render_template('add_money.html')

@app.route('/investments')
def investments():
    return render_template('investments.html')

@app.route('/send_money')
def send_money():
    return render_template('send_money.html')

@app.route('/investment_confirmation.html')
def investment_confirmation():
    return render_template('investment_confirmation.html')

@app.route('/utility')
def utility():
    return render_template('utility.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/donations')
def donations():
    return render_template('donations.html')

@app.route('/loan')
def loan():
    return render_template('loan.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/send_money_int')
def send_money_int():
    return render_template('send_money_int.html')

@app.route('/int_money_confirm')
def int_money_confirm():
    return render_template('int_money_confirm.html')

@app.route('/investmentconfirmation')
def investmentconfirmation():
    return render_template('investment_confirmation.html')

@app.route('/admin_req_submitted')
def admin_req_submitted():
    return render_template('admin_req_submitted.html')

@app.route('/scheduled_transactions')
def scheduled_transactions():
    return render_template('scheduled_transactions.html')

@app.route('/pending_installments')
def pending_installments():
    return render_template('pending_installments.html')

@app.route('/account_suspended')
def account_suspended():
    return render_template('account_suspended.html')


# ── Background workers (identical to original app.py) ─────────────────────────

def process_scheduled_transactions():
    """Mirror of the background worker from original app.py."""
    from models.database import get_db
    from models.transaction_model import (get_scheduled_transactions,
                                          update_scheduled_transaction_status,
                                          insert_send_money,
                                          generate_unique_trx_id)
    from models.user_model import get_user_by_phone
    import time
    from datetime import date
    while True:
        try:
            pending = get_scheduled_transactions()
            today = date.today()
            for trx in pending:
                if trx['schedule_date'] <= today:
                    recipient = get_user_by_phone(trx['recipient_phone'])
                    if recipient:
                        tid = generate_unique_trx_id()
                        insert_send_money(trx['user_id'], recipient['user_id'],
                                          trx['amount'], tid)
                    update_scheduled_transaction_status(trx['id'], 'processed')
        except Exception:
            pass
        time.sleep(60)


def process_matured_investments():
    """Mirror of the background worker from original app.py."""
    from models.investment_model import get_matured_investments, complete_investment
    import time
    while True:
        try:
            matured = get_matured_investments()
            for inv in matured:
                payout = float(inv['amount']) * (1 + float(inv.get('interest_rate', 0.05)))
                complete_investment(inv['id'], inv['user_id'], payout)
        except Exception:
            pass
        time.sleep(3600)


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=process_scheduled_transactions, daemon=True).start()
        threading.Thread(target=process_matured_investments, daemon=True).start()
    app.run(port=8000, debug=True)
