"""
controllers/investment_controller.py  — FIXED
current_investments: JOIN with investment_ads to get name, roi fields
"""
from flask import Blueprint, request, redirect, render_template, jsonify
from models.database import get_db
from controllers.auth_controller import get_user_id_from_cookie
import random, string, traceback
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
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM investment_ads")
        options = cursor.fetchall()
    return jsonify(options)

@investment_bp.route('/api/submit-investment', methods=['POST'])
def submit_investment():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data      = request.get_json() or {}
    option_id = data.get('option_id')
    amount    = data.get('amount')
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM investment_ads WHERE investment_id=%s", (option_id,))
            option = cursor.fetchone()
            if not option:
                return jsonify({'success': False, 'message': 'Invalid option'})
            cursor.execute("SELECT balance FROM user_profile WHERE user_id=%s", (user_id,))
            user = cursor.fetchone()
            if float(user['balance']) < float(amount):
                return jsonify({'success': False, 'message': 'Insufficient balance'})
            trx_id       = _generate_trx_id()
            start_date   = date.today()
            end_date     = start_date + relativedelta(months=int(option.get('duration', 6)))
            return_amount = round(float(amount) * (1 + float(option['roi'])/100), 2)
            cursor.execute("""
                INSERT INTO investment_user
                (user_id,investment_id,trx_id,amount,return_amount,period,start_date,end_date,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'active')
            """, (user_id, option_id, trx_id, amount, return_amount, option.get('duration',6), start_date, end_date))
            cursor.execute("UPDATE user_profile SET balance=balance-%s WHERE user_id=%s", (amount, user_id))
            cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                           (user_id, f"Investment of {amount} BDT placed. TRX: {trx_id}"))
            db.commit()
        return jsonify({'success': True, 'trx_id': trx_id})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@investment_bp.route('/api/get-latest-investment')
def get_latest_investment():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify(None)
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT iu.trx_id, ia.name, ia.roi, iu.amount, iu.return_amount,
                   iu.period, iu.start_date, iu.end_date
            FROM investment_user iu
            JOIN investment_ads ia ON iu.investment_id=ia.investment_id
            WHERE iu.user_id=%s ORDER BY iu.start_date DESC LIMIT 1
        """, (user_id,))
        inv = cursor.fetchone()
    if inv:
        inv = {k: str(v) if hasattr(v,'isoformat') else v for k,v in inv.items()}
    return jsonify(inv)

@investment_bp.route('/current_investments')
def current_investments():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    investments = []
    try:
        with db.cursor() as cursor:
            # template: for inv in investments — inv.trx_id, inv.name, inv.roi, inv.amount,
            #           inv.period, inv.start_date, inv.end_date, inv.return_amount
            cursor.execute("""
                SELECT iu.trx_id, ia.name, ia.roi, iu.amount, iu.period,
                       iu.start_date, iu.end_date, iu.return_amount
                FROM investment_user iu
                JOIN investment_ads ia ON iu.investment_id=ia.investment_id
                WHERE iu.user_id=%s AND iu.status='active'
                ORDER BY iu.start_date DESC
            """, (user_id,))
            investments = cursor.fetchall()
    except Exception:
        traceback.print_exc()
    return render_template('current_investments.html', investments=investments)
