from functools import wraps

from flask import g, redirect, session, url_for

from ..extensions import db
from ..models import User


def load_current_user():
    user_id = session.get("user_id")
    g.current_user = db.session.get(User, user_id) if user_id else None
    return g.current_user


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if load_current_user() is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view
