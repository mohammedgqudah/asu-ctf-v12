from flask import Flask, render_template, request, g, redirect, flash, session, Response
import secrets
import sqlite3
import difflib
import html

DATABASE = "./database.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(100)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


with app.app_context():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pastes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT,
            content TEXT,
            filename TEXT
        )
    """)
    db.commit()


@app.before_request
def login_as_guest():
    if "username" not in session:
        session["username"] = f"Guest-{secrets.token_hex(5)}"


@app.get("/")
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, author, filename, content FROM pastes WHERE author = ?",
        (session["username"],),
    )
    pastes = cursor.fetchall()

    host = request.headers.get('Host', request.host)

    return render_template("index.html", username=session["username"], pastes=pastes, host=host, filename=secrets.token_hex(10) + '.txt')


@app.post("/")
def add_paste():
    db = get_db()
    cursor = db.cursor()

    if "filename" not in request.form or "content" not in request.form:
        flash("Missing data", "error")
        return redirect(request.url)

    filename = request.form["filename"]
    cursor.execute(
        "INSERT INTO pastes (content, filename, author) VALUES (?, ?, ?)",
        (request.form["content"], filename, session["username"]),
    )
    db.commit()

    return redirect("/")


@app.get("/paste/<int:id>")
def view_paste(id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT content FROM pastes WHERE author = ? AND id = ?",
        (session["username"], id),
    )
    paste = cursor.fetchone()

    if not paste:
        return redirect("/")

    return Response(paste[0], mimetype="text/plain")


@app.get("/compare_pastes")
def compare():
    if "paste1" not in request.args or "paste2" not in request.args:
        flash("Missing paste1 or paste2", "error")
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT content, filename FROM pastes WHERE id in (?, ?)",
        (request.args["paste1"], request.args["paste2"]),
    )
    pastes = cursor.fetchall()
    if len(pastes) != 2:
        flash("diff: Paste(s) not found", "error")
        return redirect("/")

    diff = difflib.HtmlDiff()
    html_out = diff.make_file(
        pastes[0][0].split("\n"), pastes[1][0].split("\n"), pastes[0][1], pastes[1][1]
    )
    title = f"Pastebin -- Diff: {html.escape(pastes[0][1])}/{html.escape(pastes[1][1])}"
    html_out = html_out.replace("<title></title>", f"<title>{title}</title>")
    html_out = html_out.replace("<body>", f"<body>\n<h1>{title}</h1>")
    return html_out


app.run("0.0.0.0", port=5002, debug=True)
