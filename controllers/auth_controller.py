"""
controllers/auth_controller.py
Handles: login, signup, logout, admin login/signup.
All original route logic is preserved exactly; only the DB calls are
delegated to models.
"""
from flask import Blueprint, request, redirect, render_template, flash, make_response
from models.database import get_db
import bcrypt

auth_bp = Blueprint('auth', __name__)


# ── Helper ─────────────────────────────────────────────────────────────────────

def get_user_id_from_cookie():
    return request.cookies.get("user_id")

def set_secure_cookie(response, user_id):
    response.set_cookie("user_id", str(user_id), max_age=3600,
                        httponly=True, secure=True, samesite='Strict')
    return response


# ── Routes ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    resp = make_response(redirect("/login"))
    resp.delete_cookie("user_id")
    return resp


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    phone = request.form.get("phone")
    password = request.form.get("password")

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM user_profile WHERE phone_number = %s", (phone,))
        user = cursor.fetchone()

    if not user:
        flash("User not found.", "error")
        return render_template("login.html")

    if user.get("status") == "suspended":
        return render_template("account_suspended.html")

    if bcrypt.checkpw(password.encode(), user["password"].encode()):
        resp = make_response(redirect("/home"))
        set_secure_cookie(resp, user["user_id"])
        return resp
    else:
        flash("Invalid credentials.", "error")
        return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    first_name = request.form.get("firstName")
    last_name = request.form.get("lastName")
    phone = request.form.get("phone")
    password = request.form.get("password")
    dob = request.form.get("dob")
    email = request.form.get("email")
    nid = request.form.get("nid")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO user_profile
                   (first_name, last_name, phone_number, password, dob, email, nid, balance, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 'active')""",
                (first_name, last_name, phone, hashed, dob, email, nid)
            )
        db.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect("/login")
    except Exception as e:
        flash(f"Registration failed: {str(e)}", "error")
        return render_template("signup.html")


@auth_bp.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    phone = request.form.get("phone")
    password = request.form.get("password")

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM admin_profile WHERE phone_number = %s", (phone,))
        admin = cursor.fetchone()

    if not admin:
        flash("Admin not found.", "error")
        return render_template("admin_login.html")

    if admin.get("status") != "authorized":
        flash("Your admin account is not yet authorized.", "warning")
        return render_template("admin_login.html")

    if bcrypt.checkpw(password.encode(), admin["password"].encode()):
        resp = make_response(redirect("/admin_home"))
        resp.set_cookie("admin_id", str(admin["admin_id"]), max_age=3600,
                        httponly=True, secure=True, samesite='Strict')
        return resp
    else:
        flash("Invalid credentials.", "error")
        return render_template("admin_login.html")


@auth_bp.route("/admin_signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "GET":
        return render_template("admin_signup.html")

    first_name = request.form.get("firstName")
    last_name = request.form.get("lastName")
    phone = request.form.get("phone")
    password = request.form.get("password")
    email = request.form.get("email")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO admin_profile
                   (first_name, last_name, phone_number, password, email, status)
                   VALUES (%s, %s, %s, %s, %s, 'unauthorized')""",
                (first_name, last_name, phone, hashed, email)
            )
        db.commit()
        return redirect("/admin_req_submitted")
    except Exception as e:
        flash(f"Signup failed: {str(e)}", "error")
        return render_template("admin_signup.html")
