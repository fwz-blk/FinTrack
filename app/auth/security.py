from datetime import timedelta

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def password_error(password):
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not any(character.isupper() for character in password):
        return "Password must include an uppercase letter."
    if not any(character.islower() for character in password):
        return "Password must include a lowercase letter."
    if not any(character.isdigit() for character in password):
        return "Password must include a number."
    return None


def make_token(purpose, user):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps({"purpose": purpose, "user_id": user.id, "version": user.reset_token_version})


def read_token(purpose, token, max_age=timedelta(hours=1).total_seconds()):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        payload = serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    if payload.get("purpose") != purpose:
        return None
    return payload
