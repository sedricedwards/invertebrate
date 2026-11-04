from functools import wraps
from flask import request, abort, g

def require_auth(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        token = request.headers.get("Authorization", "")
        user = lookup_token(token.removeprefix("Bearer "))
        if user is None:
            abort(401)
        g.user = user
        return fn(*a, **kw)
    return wrapper

def lookup_token(token):
    from app.db import TOKENS
    return TOKENS.get(token)
