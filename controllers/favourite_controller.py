"""
controllers/favourite_controller.py  — FIXED
saved_contacts variable name matches template exactly.
"""
from flask import Blueprint, request, redirect, render_template
from models.database import get_db
from controllers.auth_controller import get_user_id_from_cookie

favourite_bp = Blueprint('favourite', __name__)

@favourite_bp.route('/favourite_accounts')
def favourite_accounts():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    search_query = request.args.get('search', '').strip()
    db = get_db()
    with db.cursor() as cursor:
        if search_query:
            cursor.execute("""
                SELECT name, phone FROM saved_details
                WHERE user_id=%s AND (name LIKE %s OR phone LIKE %s)
            """, (user_id, f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT name, phone FROM saved_details WHERE user_id=%s", (user_id,))
        # template: for contact in saved_contacts — contact.name, contact.phone
        saved_contacts = cursor.fetchall()
    return render_template('favourite_accounts.html', saved_contacts=saved_contacts)

@favourite_bp.route('/delete_contact', methods=['POST'])
def delete_contact():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    phone = request.form.get('phone')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM saved_details WHERE phone=%s AND user_id=%s", (phone, user_id))
    db.commit()
    return redirect('/favourite_accounts')
