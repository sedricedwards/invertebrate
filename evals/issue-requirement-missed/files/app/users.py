import hashlib

from app.store import db


def set_password(user_id, password):
    db.users[user_id] = {"password_sha256": hashlib.sha256(password.encode()).hexdigest()}
