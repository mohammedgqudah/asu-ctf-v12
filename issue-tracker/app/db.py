import sqlite3
import uuid
from flask import g, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, csv

db_path = "project.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db


def db_init():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        status TEXT NOT NULL
            CHECK(status IN ('pending','in progress','done'))
            DEFAULT 'pending'
    );
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS exports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()


def register_user(username: str, password: str) -> bool:
    db = get_db()
    hashed = generate_password_hash(password)
    try:
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(username: str, password: str) -> bool:
    db = get_db()
    user = db.execute(
        "SELECT id, username, password FROM users WHERE username = ?", (username,)
    ).fetchone()
    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return True
    return False


def add_task(title: str, content: str) -> int:
    user_id = session["user_id"]
    db = get_db()
    cursor = db.execute(
        "INSERT INTO tasks (user_id, title, content) VALUES (?, ?, ?)",
        (user_id, title, content),
    )
    db.commit()
    return cursor.lastrowid


def change_task_status(task_id: int, status: str) -> None:
    if status not in ("pending", "in progress", "done"):
        raise ValueError(f"Invalid status: {status}")
    db = get_db()
    db.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    db.commit()


def move(task_id: int):
    db = get_db()
    row = db.execute(
        "SELECT id, title, content, status FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not row:
        return
    if row[3] == "pending":
        next = "in progress"
    elif row[3] == "in progress":
        next = "done"
    else:
        next = "done"
    change_task_status(task_id, next)


def list_tasks(user_id: int = None) -> dict[str, list[dict]]:
    db = get_db()

    rows = db.execute(
        "SELECT id, title, content, status FROM tasks ORDER BY id",
    ).fetchall()

    result = {"pending": [], "in_progress": [], "done": []}

    status_map = {"pending": "pending", "in progress": "in_progress", "done": "done"}

    for row in rows:
        key = status_map.get(row["status"], row["status"])
        result[key].append(
            {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "status": row["status"],
            }
        )

    return result


def create_export() -> int:
    db = get_db()
    filename = f"{uuid.uuid4()}.csv"
    cursor = db.execute("INSERT INTO exports (filename) VALUES (?)", (filename,))
    db.commit()
    return cursor.lastrowid


def list_exports() -> list[dict]:
    db = get_db()
    rows = db.execute(
        "SELECT id, filename, created_at FROM exports ORDER BY created_at DESC"
    ).fetchall()

    exports = []
    for row in rows:
        exports.append(
            {
                "id": row["id"],
                "filename": row["filename"],
                "created_at": row["created_at"],
                "url": f"/static/{row['filename']}",
            }
        )
    return exports


def perform_export(export_id: int) -> None:
    db = get_db()
    exp = db.execute(
        "SELECT filename FROM exports WHERE id = ?", (export_id,)
    ).fetchone()
    if not exp:
        raise RuntimeError(f"Export job {export_id} not found")

    tasks = db.execute(
        "SELECT id, title, content, status FROM tasks ORDER BY id"
    ).fetchall()

    filepath = os.path.join("./static", exp["filename"])
    now = datetime.now().isoformat()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "content", "status", "exported_at"])
        for t in tasks:
            writer.writerow([t["id"], t["title"], t["content"], t["status"], now])
