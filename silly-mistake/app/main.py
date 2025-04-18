from flask import Flask, render_template, request, g, redirect, flash, make_response, request_finished
import secrets
import sqlite3
import os
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import jwt

DATABASE = "./database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(100)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# check if the user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "token" not in request.cookies:
            return redirect("/login")
        try:
            request.user = jwt.decode(
                request.cookies.get("token"),
                app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


with app.app_context():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            author TEXT
        )
    """)

    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM notes")

    cursor.execute(
        "INSERT INTO users (id, username, password) VALUES (1, ?, ?)",
        ("admin", generate_password_hash(secrets.token_hex(100))),
    )
    cursor.execute(
        "INSERT INTO notes (content, author) VALUES (?, ?)",
        (os.environ.get("FLAG", "ASU{testing_flag}"), "admin"),
    )
    db.commit()


@app.get("/")
@login_required
def index():
    share_link = ''
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT content, author FROM notes WHERE author = ?",
        (request.user["username"],),
    )
    notes = cursor.fetchall()

    if request.args.get("share_with"):
        share_with = request.args["share_with"]
        cursor.execute("SELECT 1 FROM users where username = ?", (share_with,))
        if not cursor.fetchone():
            flash(
                f"Unable to share notes with '{share_with}'. Are you share you spelled it correctly?",
                "error",
            )
        else:
            share_token = jwt.encode(
                {"username": share_with, "author": request.user["username"]},
                app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            share_link = f"{request.host_url}view_shared?key={share_token}"

    return render_template("index.html", username=request.user["username"], notes=notes, share_link=share_link)


@app.get("/view_shared")
@login_required
def view_shared():
    if 'key' not in request.args:
        return redirect("/")
    key = request.args['key']
    try:
        share = jwt.decode(
            key,
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
    except:
        return redirect("/")

    if share['username'] != request.user['username']:
        flash(f"This public link belongs to another user ('{share['username']}') and cannot be used with your account.", 'error')
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT content, author FROM notes WHERE author = ?",
        (share['author'],),
    )
    notes = cursor.fetchall()

    return render_template("view_shared.html", author=share['author'], notes=notes)

@app.post("/")
@login_required
def add_note():
    db = get_db()
    cursor = db.cursor()
    if "note" not in request.form:
        flash("Missing note", "error")
        return redirect(request.url)

    cursor.execute(
        "INSERT INTO notes (content, author) VALUES (?, ?)",
        (request.form["note"], request.user["username"]),
    )
    db.commit()

    return redirect("/")


# Authentication


@app.get("/register")
def render_register():
    return render_template("register.html")


@app.post("/register")
def register():
    data = request.form

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        flash("Missing username or password")
        return redirect(request.url), 400

    db = get_db()
    cursor = db.cursor()

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        flash("Username already exists")
        return redirect(request.url)

    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hashed_password),
    )
    db.commit()

    flash("User registered successfully.")
    return redirect("/login")


@app.get("/login")
def render_login():
    return render_template("login.html")


@app.post("/login")
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        flash("Username and password are required.", "error")
        return redirect(request.url)

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, username, password FROM users WHERE username = ?", (username,)
    )
    user = cursor.fetchone()

    if not user or not check_password_hash(user[2], password):
        flash("Invalid username or password.", "error")
        return redirect(request.url)

    resp = make_response(redirect("/"))
    resp.set_cookie(
        "token",
        jwt.encode({"username": user[1]}, app.config["SECRET_KEY"], algorithm="HS256"),
    )

    flash("Login successful!", "success")

    return resp


app.run("0.0.0.0", 3000)
