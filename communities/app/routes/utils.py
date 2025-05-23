from flask import session, redirect
from functools import wraps


# check if the user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session["user_id"] is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
