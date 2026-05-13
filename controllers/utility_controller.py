"""
controllers/utility_controller.py  — FIXED
Passes popup variable exactly as templates expect: popup="success"/"insufficient"/"limit"
"""
from flask import Blueprint, request, redirect, render_template
from models.database import get_db
from controllers.auth_controller import get_user_id_from_cookie
from datetime import datetime, timedelta
import traceback

utility_bp = Blueprint('utility', __name__)

def _pay_bill(user_id, table, id_col, id_val, name, amount, month,
              is_installment, installment_months, is_multi, mobile_pct, extra_cols):
    """Shared payment logic for gas/electricity/wifi."""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT balance, transaction_limit FROM user_profile WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return "insufficient"
        balance  = float(user['balance'])
        trx_limit = float(user['transaction_limit'] or 999999)
        amount_f  = float(amount)

        if is_installment and installment_months:
            months = int(installment_months)
            part   = round(amount_f / months, 2)
            if balance < part:
                return "insufficient"
            if part > trx_limit:
                return "limit"
            cursor.execute("UPDATE user_profile SET balance=balance-%s WHERE user_id=%s", (part, user_id))
            due_1 = (datetime.now() + timedelta(days=30)).date()
            due_2 = (datetime.now() + timedelta(days=60)).date() if months == 3 else None
            cols  = f"user_id, name, {id_col}, amount, month, installment, due_1, due_2, status"
            vals  = (user_id, name, id_val, amount_f, month, months, due_1, due_2, 'pending')
            cursor.execute(f"INSERT INTO {table} ({cols}) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", vals)
        elif is_multi:
            mobile_share = round((mobile_pct / 100) * amount_f, 2)
            if balance < mobile_share:
                return "insufficient"
            if mobile_share > trx_limit:
                return "limit"
            cursor.execute("UPDATE user_profile SET balance=balance-%s WHERE user_id=%s", (mobile_share, user_id))
            cursor.execute(f"INSERT INTO {table} (user_id, name, {id_col}, amount, month, multi_source) VALUES (%s,%s,%s,%s,%s,%s)",
                           (user_id, name, id_val, amount_f, month, f"{mobile_pct}% mobile"))
        else:
            if balance < amount_f:
                return "insufficient"
            if amount_f > trx_limit:
                return "limit"
            cursor.execute("UPDATE user_profile SET balance=balance-%s WHERE user_id=%s", (amount_f, user_id))
            cursor.execute(f"INSERT INTO {table} (user_id, name, {id_col}, amount, month) VALUES (%s,%s,%s,%s,%s)",
                           (user_id, name, id_val, amount_f, month))

        cursor.execute("UPDATE user_profile SET points=points+%s WHERE user_id=%s", (int(amount_f//100), user_id))
        cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                       (user_id, f"Bill payment of {amount_f} BDT successful."))
        cursor.execute("INSERT INTO history (user_id,type,trx_id,account,amount) VALUES (%s,%s,'N/A',%s,%s)",
                       (user_id, f"{table.replace('pay_','').title()} Bill", id_val, -amount_f))
        db.commit()
    return "success"

# ── Gas Bill ───────────────────────────────────────────────────────────────────
@utility_bp.route('/gas_bill', methods=['GET', 'POST'])
def gas_bill():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    if request.method == 'GET':
        return render_template('gas_bill.html')
    name       = request.form.get('userName')
    meter_no   = request.form.get('meterNo')
    amount     = request.form.get('amount')
    month      = request.form.get('month')
    is_inst    = request.form.get('installmentOption') == 'on'
    inst_mo    = request.form.get('installmentMonths')
    is_multi   = request.form.get('multipleSourceOption') == 'on'
    mobile_pct = int(request.form.get('mobileSlider', 0)) if is_multi else 100
    result = _pay_bill(user_id, 'pay_gas', 'meter_no', meter_no, name, amount, month,
                       is_inst, inst_mo, is_multi, mobile_pct, {})
    # template: popup="success"/"insufficient"/"limit"
    return render_template('gas_bill.html', popup=result)

# ── Electricity Bill ───────────────────────────────────────────────────────────
@utility_bp.route('/electricity_bill', methods=['GET', 'POST'])
def electricity_bill():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    if request.method == 'GET':
        return render_template('electricity_bill.html')
    name       = request.form.get('userName')
    meter_no   = request.form.get('meterNo')
    amount     = request.form.get('amount')
    month      = request.form.get('month')
    is_inst    = request.form.get('installmentOption') == 'on'
    inst_mo    = request.form.get('installmentMonths')
    is_multi   = request.form.get('multipleSourceOption') == 'on'
    mobile_pct = int(request.form.get('mobileSlider', 0)) if is_multi else 100
    result = _pay_bill(user_id, 'pay_electricity', 'meter_no', meter_no, name, amount, month,
                       is_inst, inst_mo, is_multi, mobile_pct, {})
    return render_template('electricity_bill.html', popup=result)

# ── WiFi Bill ──────────────────────────────────────────────────────────────────
@utility_bp.route('/wifi_bill', methods=['GET', 'POST'])
def wifi_bill():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    if request.method == 'GET':
        return render_template('wifi_bill.html')
    name       = request.form.get('userName')
    wifi_id    = request.form.get('meterNo')          # form field same name
    amount     = request.form.get('amount')
    month      = request.form.get('month')
    is_inst    = request.form.get('installmentOption') == 'on'
    inst_mo    = request.form.get('installmentMonths')
    is_multi   = request.form.get('multipleSourceOption') == 'on'
    mobile_pct = int(request.form.get('mobileSlider', 0)) if is_multi else 100
    result = _pay_bill(user_id, 'pay_wifi', 'wifi_id', wifi_id, name, amount, month,
                       is_inst, inst_mo, is_multi, mobile_pct, {})
    return render_template('wifi_bill.html', popup=result)
