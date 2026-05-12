"""
controllers/favourite_controller.py
Handles: favourite/saved accounts.
"""
from flask import Blueprint, request, redirect, render_template
from models import favourite_model
from controllers.auth_controller import get_user_id_from_cookie

favourite_bp = Blueprint('favourite', __name__)


@favourite_bp.route('/favourite_accounts', methods=['GET', 'POST'])
def favourite_accounts():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    search_query = request.args.get('search', '').strip()
    saved_contacts = favourite_model.get_saved_contacts(user_id, search_query or None)
    return render_template('favourite_accounts.html', saved_contacts=saved_contacts)


@favourite_bp.route('/delete_contact', methods=['POST'])
def delete_contact():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect('/login')

    phone = request.form['phone']
    favourite_model.delete_saved_contact(user_id, phone)
    return redirect('/favourite_accounts')
