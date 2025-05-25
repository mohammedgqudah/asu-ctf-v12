from flask import Blueprint, flash, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

from models.base import db
from models.user import User
import re

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/register")
def render_register():
    return render_template("register.html")


@auth_bp.post("/register")
def register():
    data = request.form

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        flash("Missing username or password")
        return redirect(request.url)

    if not re.match("^[a-zA-Z0-9_]+$",username):
        flash("Symbols are not allowed.")
        return redirect(request.url)

    existing_user = db.session.query(User).filter_by(username=username).first()
    if existing_user:
        flash("Username already exists")
        return redirect(request.url)

    hashed_password = generate_password_hash(password)

    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    flash("User registered successfully.")
    return redirect("/login")


@auth_bp.get("/login")
def render_login():
    return render_template("login.html")


@auth_bp.post("/login")
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(request.url)

    user = db.session.query(User).filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        flash("Invalid username or password.", "error")
        return redirect(request.url)

    session["user_id"] = str(user.id)
    session["username"] = user.username
    return redirect("/")
