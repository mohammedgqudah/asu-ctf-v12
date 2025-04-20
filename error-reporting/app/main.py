from flask import Flask, render_template, request, g, redirect, flash, session
import secrets
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os

DATABASE = "./database.db"

def log_per_user(username: str, log: str):
    log_path = os.path.join('logs', f'{secure_filename(username)}.log')
    with open(log_path, 'a') as f:
        f.write(log + '\n')

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
        if "username" not in session:
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

    cursor.execute("DELETE FROM users")

    cursor.execute(
        "INSERT INTO users (id, username, password) VALUES (1, ?, ?)",
        ("admin", generate_password_hash(secrets.token_hex(100))),
    )
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (os.getenv('FLAG', 'ASU{this_is_a_very_long_test_flag_i_repeat_a_test_flag}'), generate_password_hash(secrets.token_hex(100))),
    )
    db.commit()

@app.get("/")
@login_required
def index():
    return render_template("index.html", username=session['username'], user_id=session['user_id'])

@app.get("/logs")
@login_required
def admin():
    with open(os.path.join('logs', secure_filename(session['username']) + '.log')) as f:
        logs = f.read()

    return render_template("logs.html", logs=logs)

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

    log_per_user(username, f"User `{username}` registered successfully")

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


    session['username'] = user[1]
    session['user_id'] = user[0]
    flash("Login successful!", "success")

    return redirect("/")


@app.post("/friend")
@login_required
def friend_request():
    try:
        username = request.form.get("username")

        if not username:
            flash("Username is required.", "error")
            return redirect(request.url)

        db = get_db()
        cursor = db.cursor()

        query = f"SELECT id, username, password FROM users WHERE username = '{username}'"
        cursor.execute(query)
        user = cursor.fetchone()
        print(f"...Sending friend request to user {user[0]}")

        log_per_user(session['username'], f'Friend request sent')
    except Exception as e:
        pass

    flash("If this account exists, a friend request was sent to them.", "success")

    return redirect("/")

#app.run("0.0.0.0", 5003)
