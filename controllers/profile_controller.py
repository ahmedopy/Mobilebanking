"""
controllers/profile_controller.py  — FIXED
transaction_limit passed as plain float, not dict row.
"""
from flask import Blueprint, request, redirect, render_template, flash, url_for, jsonify
from models.database import get_db
from controllers.auth_controller import get_user_id_from_cookie
import os
from werkzeug.utils import secure_filename

profile_bp    = Blueprint('profile', __name__)
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# ── Profile ────────────────────────────────────────────────────────────────────
@profile_bp.route('/profile')
def profile():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user_profile WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
    if not user:
        return "User not found", 404
    # template uses profile as tojson with keys: username,name,phone,balance,firstName,lastName,dob,email,nid,loyaltyPoints,profilePic
    profile_data = {
        'username':      f"{user['first_name']} {user['last_name']}",
        'name':          f"{user['first_name']} {user['last_name']}",
        'phone':         user['phone_number'],
        'balance':       float(user['balance'] or 0),
        'firstName':     user['first_name'],
        'lastName':      user['last_name'],
        'dob':           str(user['dob']) if user['dob'] else '',
        'email':         user['email'] or '',
        'nid':           user['nid'] or '',
        'loyaltyPoints': user.get('points') or 0,
        'profilePic':    user.get('profile_pic') or 'default-profile-pic.jpg',
    }
    return render_template('profile.html', profile=profile_data)

# ── Edit Profile ───────────────────────────────────────────────────────────────
@profile_bp.route('/editprofile', methods=['GET'])
def edit_profile():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user_profile WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
    if not user:
        return redirect('/home')
    # template: profile.name, profile.phone, profile.firstName, profile.lastName, profile.dob, profile.email, profile.nid
    profile_data = {
        'name':      f"{user['first_name']} {user['last_name']}",
        'phone':     user['phone_number'],
        'firstName': user['first_name'],
        'lastName':  user['last_name'],
        'dob':       user['dob'].strftime('%Y-%m-%d') if user['dob'] else '',
        'email':     user['email'] or '',
        'nid':       user['nid'] or '',
        'profile_pic': user.get('profile_pic') or 'default-profile-pic.jpg',
    }
    return render_template('editprofile.html', profile=profile_data)

@profile_bp.route('/updateprofile', methods=['POST'])
def update_profile():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    first_name  = request.form.get('firstName', '')
    last_name   = request.form.get('lastName', '')
    dob         = request.form.get('dob', '')
    email       = request.form.get('email', '')
    nid         = request.form.get('nid', '')
    profile_pic = None
    if 'profilePic' in request.files:
        file = request.files['profilePic']
        if file and allowed_file(file.filename):
            filename  = secure_filename(file.filename)
            folder    = 'static/uploads'
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, filename))
            profile_pic = filename
    db = get_db()
    try:
        with db.cursor() as cursor:
            if profile_pic:
                cursor.execute("""
                    UPDATE user_profile SET first_name=%s, last_name=%s, dob=%s, email=%s, nid=%s, profile_pic=%s
                    WHERE user_id=%s
                """, (first_name, last_name, dob, email, nid, profile_pic, user_id))
            else:
                cursor.execute("""
                    UPDATE user_profile SET first_name=%s, last_name=%s, dob=%s, email=%s, nid=%s
                    WHERE user_id=%s
                """, (first_name, last_name, dob, email, nid, user_id))
            db.commit()
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('profile.edit_profile'))

# ── Transaction Limit ──────────────────────────────────────────────────────────
@profile_bp.route('/set_limit', methods=['GET', 'POST'])
def set_limit():
    user_id = get_user_id_from_cookie()
    if not user_id:
        return redirect('/login')
    db = get_db()
    if request.method == 'GET':
        with db.cursor() as cursor:
            cursor.execute("SELECT transaction_limit FROM user_profile WHERE user_id=%s", (user_id,))
            row = cursor.fetchone()
        # template: transaction_limit as plain float value
        transaction_limit = float(row['transaction_limit'] or 0) if row else 0
        return render_template('transaction_limit.html', transaction_limit=transaction_limit)

    data        = request.get_json(silent=True) or {}
    limit_amount = data.get('limit') or request.form.get('limit_amount')
    try:
        with db.cursor() as cursor:
            cursor.execute("UPDATE user_profile SET transaction_limit=%s WHERE user_id=%s",
                           (limit_amount, user_id))
            db.commit()
        return jsonify({'success': True, 'message': 'Transaction limit updated.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ── Upload Profile Picture ─────────────────────────────────────────────────────
@profile_bp.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    user_id = get_user_id_from_cookie()
    if not user_id or 'profilePic' not in request.files:
        return jsonify({"success": False, "message": "Unauthorized or no file"})
    file = request.files['profilePic']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"})
    try:
        filename     = secure_filename(file.filename)
        ext          = os.path.splitext(filename)[1]
        new_filename = f"{user_id}_profile{ext}"
        upload_path  = os.path.join("static/uploads", new_filename)
        os.makedirs("static/uploads", exist_ok=True)
        file.save(upload_path)
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("UPDATE user_profile SET profile_pic=%s WHERE user_id=%s", (new_filename, user_id))
            db.commit()
        return jsonify({"success": True, "image_url": f"/static/uploads/{new_filename}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
