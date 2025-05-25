from flask import Flask, abort, g, session, redirect, url_for, request
import secrets
from models.base import db
from models.user import User
from models.community import Community
from models.post import Post
from routes.auth import auth_bp
from routes.communities import bp as comm_bp
import os

from routes.utils import login_required

app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(100)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///communities.db"

app.register_blueprint(auth_bp)
app.register_blueprint(comm_bp)

db.init_app(app)

with app.app_context():
    db.drop_all()
    db.create_all()


@app.get('/flag')
@login_required
def flag():
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        return abort(401)

    return str(os.getenv('FLAG'))

app.run("0.0.0.0", port=5006)
