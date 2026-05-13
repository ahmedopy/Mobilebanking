"""
controllers/loan_controller.py  — FIXED
"""
from flask import Blueprint, request, redirect, render_template, jsonify, flash
from models.database import get_db
from controllers.auth_controller import get_user_id_from_cookie
import random, string, traceback

loan_bp = Blueprint('loan', __name__)

def _generate_trx_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ── Request Loan (API called from loan.html JS) ────────────────────────────────
@loan_bp.route('/api/request-loan', methods=['POST'])
def request_loan():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data        = request.get_json() or {}
    amount      = data.get('amount')
    duration    = data.get('duration', 12)
    purpose     = data.get('purpose', '')
    trx_id      = _generate_trx_id()
    try:
        amount_f    = float(amount)
        interest    = 10.0
        return_amt  = round(amount_f * (1 + interest/100), 2)
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO loans (user_id,trx_id,loan_amount,interest_rate,duration,return_amount,status,remarks)
                VALUES (%s,%s,%s,%s,%s,%s,'pending',%s)
            """, (user_id, trx_id, amount_f, interest, duration, return_amt, purpose))
            db.commit()
        return jsonify({'success': True, 'trx_id': trx_id})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

# ── Approve Loans (admin) ──────────────────────────────────────────────────────
@loan_bp.route('/approve_loans', methods=['GET', 'POST'])
def approve_loans():
    db = get_db()
    if request.method == 'GET':
        with db.cursor() as cursor:
            # template: for loan in pending_loans — fields: user_id,loan_amount,duration,return_amount,trx_id
            cursor.execute("""
                SELECT user_id, trx_id, loan_amount, duration, return_amount
                FROM loans WHERE status='pending'
            """)
            pending_loans = cursor.fetchall()
        return render_template('approve_loans.html', pending_loans=pending_loans)

    # POST — handle approve/deny for each loan
    trx_ids  = request.form.getlist('trx_ids[]')
    with db.cursor() as cursor:
        for i, trx_id in enumerate(trx_ids):
            action = request.form.get(f'statuses_{i}', '')
            if action == 'Approve':
                cursor.execute("SELECT user_id, loan_amount FROM loans WHERE trx_id=%s", (trx_id,))
                loan = cursor.fetchone()
                if loan:
                    cursor.execute("UPDATE loans SET status='approved' WHERE trx_id=%s", (trx_id,))
                    cursor.execute("UPDATE user_profile SET balance=balance+%s WHERE user_id=%s",
                                   (loan['loan_amount'], loan['user_id']))
                    cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                                   (loan['user_id'], f"Loan of {loan['loan_amount']} BDT approved!"))
            elif action == 'Deny':
                cursor.execute("UPDATE loans SET status='denied' WHERE trx_id=%s", (trx_id,))
        db.commit()
    flash('Loans updated.', 'success')
    return redirect('/approve_loans')

# ── Active Loans (user) ────────────────────────────────────────────────────────
@loan_bp.route('/active_loans')
def active_loans():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    with db.cursor() as cursor:
        # template: for loan in active_loans — fields: trx_id,loan_amount,interest_rate,duration,issue_date,end_date,return_amount
        cursor.execute("""
            SELECT trx_id, user_id, loan_amount, interest_rate, duration,
                   issue_date, end_date, return_amount
            FROM loans WHERE user_id=%s AND status IN ('approved','pending')
        """, (user_id,))
        active_loans = cursor.fetchall()
    return render_template('active_loans.html', active_loans=active_loans)

# ── Pay Loan ───────────────────────────────────────────────────────────────────
@loan_bp.route('/pay_loan/<trx_id>', methods=['POST'])
def pay_loan(trx_id):
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT user_id, return_amount FROM loans WHERE trx_id=%s AND status='approved'", (trx_id,))
            loan = cursor.fetchone()
            if not loan:
                flash('Loan not found.', 'error')
                return redirect('/active_loans')
            cursor.execute("SELECT balance FROM user_profile WHERE user_id=%s", (user_id,))
            user = cursor.fetchone()
            if float(user['balance']) < float(loan['return_amount']):
                flash('Insufficient balance.', 'error')
                return redirect('/active_loans')
            cursor.execute("UPDATE user_profile SET balance=balance-%s WHERE user_id=%s",
                           (loan['return_amount'], user_id))
            cursor.execute("UPDATE loans SET status='paid' WHERE trx_id=%s", (trx_id,))
            cursor.execute("INSERT INTO notifications (user_id,alerts) VALUES (%s,%s)",
                           (user_id, f"Loan {trx_id} paid successfully."))
            db.commit()
        flash('Loan paid successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/active_loans')
