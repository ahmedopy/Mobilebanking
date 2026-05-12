"""
controllers/profile_controller.py
Handles: profile view/edit, profile picture upload, transaction limits.
"""
from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify
from models import user_model
from controllers.auth_controller import get_user_id_from_cookie
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route('/profile')
def profile():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    user = user_model.get_user_by_id(user_id)
    if not user:
        return "User not found", 404
    profile_data = {
        'username': f"{user['first_name']} {user['last_name']}",
        'name': f"{user['first_name']} {user['last_name']}",
        'phone': user['phone_number'],
        'balance': float(user['balance']),
        'firstName': user['first_name'],
        'lastName': user['last_name'],
        'dob': str(user['dob']) if user['dob'] else '',
        'email': user['email'],
        'nid': user['nid'],
        'loyaltyPoints': user.get('points', 0),
        'profilePic': user.get('profile_pic', 'default-profile-pic.jpg'),
    }
    return render_template('profile.html', profile=profile_data)


@profile_bp.route('/editprofile', methods=['GET'])
def edit_profile():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    user = user_model.get_user_by_id(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect('/home')
    profile_data = {
        'name': f"{user['first_name']} {user['last_name']}",
        'phone': user['phone_number'],
        'firstName': user['first_name'],
        'lastName': user['last_name'],
        'dob': user['dob'].strftime('%Y-%m-%d') if user['dob'] else '',
        'email': user['email'],
        'nid': user['nid'],
        'profile_pic': user['profile_pic'],
    }
    return render_template('editprofile.html', profile=profile_data)


@profile_bp.route('/updateprofile', methods=['POST'])
def update_profile():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    first_name = request.form['firstName']
    last_name = request.form['lastName']
    dob = request.form['dob']
    email = request.form['email']
    nid = request.form['nid']

    profile_pic = None
    if 'profilePic' in request.files:
        file = request.files['profilePic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = 'static/uploads'
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))
            profile_pic = f'/{filename}'

    try:
        user_model.update_user_profile(user_id, first_name, last_name, dob, email, nid, profile_pic)
        flash('Your Profile Updated Successfully.', 'success')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'error')

    return redirect(url_for('profile.edit_profile'))


@profile_bp.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    user_id = get_user_id_from_cookie()
    if not user_id or 'profilePic' not in request.files:
        return jsonify({"success": False, "message": "Unauthorized or no file"})

    file = request.files['profilePic']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"})

    try:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1]
        new_filename = f"{user_id}_profile{ext}"
        upload_path = os.path.join("static/uploads", new_filename)
        file.save(upload_path)
        user_model.update_profile_picture(user_id, new_filename)
        return jsonify({"success": True, "image_url": f"/static/uploads/{new_filename}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@profile_bp.route('/set_limit', methods=['GET', 'POST'])
def set_limit():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')

    if request.method == 'GET':
        limit_data = user_model.get_transaction_limit(user_id)
        return render_template('transaction_limit.html', limit=limit_data)

    limit_type = request.form.get('limit_type')
    limit_amount = request.form.get('limit_amount')
    try:
        user_model.set_transaction_limit(user_id, limit_type, limit_amount)
        flash('Transaction limit updated.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect('/set_limit')
