from flask import (
    Flask,
    render_template,
    g,
    request,
    redirect,
    url_for,
    jsonify,
    session,
    flash,
)
import re
import pathlib
from functools import wraps
from db import (
    db_init,
    add_task,
    login_user,
    register_user,
    move,
    list_tasks,
    list_exports,
    perform_export,
    create_export,
)
from werkzeug.utils import secure_filename
import os
from app_worker import celery_init_app


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


app = Flask(__name__)
celery_app = celery_init_app(app)
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["TEMPLATE_AUTO_RELOAD"] = False
app.config['ENV'] = 'production'


with app.app_context():
    for name in app.jinja_env.list_templates():
        app.jinja_env.get_template(name)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db:
        db.close()


with app.app_context():
    db_init()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.", "warning")
        elif not re.match(r'^[A-Za-z0-9]+', username):
            flash("symbols are not allowed", "warning")
        else:
            success = register_user(username, password)
            if success:
                flash("Registred!", "success")
                return redirect(url_for("login"))
            else:
                flash("Username already taken.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.", "warning")
        elif login_user(username, password):
            return redirect("/board")
        else:
            flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/board")
    return render_template("index.html")


@app.route("/board")
@login_required
def board():
    return render_template("board.html", tasks=list_tasks())


@app.route("/move/<int:task_id>")
@login_required
def do_move(task_id: int):
    move(task_id)
    return redirect("/board")


@app.route("/editor")
@login_required
def editor():
    return render_template("editor.html")


@app.post("/submit")
@login_required
def submit():
    html = request.form.get("content")
    title = request.form.get("title")
    if not html or not title:
        return redirect("/editor")
    add_task(title, html)

    return redirect("/board")


@app.get("/settings")
@login_required
def settings():
    return render_template("settings.html", exports=list_exports())


@app.post("/settings")
@login_required
def export():
    export_id = create_export()
    export_job.delay(export_id)
    return redirect("/settings")


@app.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    image = request.files.get("image")
    if not image:
        return jsonify({"error": "no file"}), 400

    filename: str = secure_filename(image.filename)
    if ".." in filename:
        return jsonify({"error": "rejected"})

    save_path = os.path.join(app.config["UPLOAD_FOLDER"], session['username'], filename)
    pathlib.Path(save_path).parent.mkdir(exist_ok=True, parents=True)
    image.save(save_path)

    url = url_for("static", filename=f"uploads/{session['username']}/{filename}")
    return jsonify({"url": url})


@celery_app.task()
def export_job(export_id):
    perform_export(export_id)
