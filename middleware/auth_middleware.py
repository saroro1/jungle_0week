from flask import request, g, redirect, url_for
from functools import wraps
from typing import Callable

from utils.jwt import Jwt


def auth_middleware(use_redirect: bool = False):
    def decorator(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')

            if not auth_header or not auth_header.startswith("Bearer "):
                return _handle_auth_fail(use_redirect)

            token = auth_header.split(" ")[1]

            if not Jwt.is_valid(token):
                return _handle_auth_fail(use_redirect)

            try:
                user_data = Jwt.decode(token)
                g.current_user = user_data  # 예: {"id": "user123"}
            except Exception as e:
                return _handle_auth_fail(e)

            return f(*args, **kwargs)
        return wrapper
    return decorator


def _handle_auth_fail(use_redirect: bool):
    if use_redirect:
        return redirect_to_login()
    else:
        return {"error": "로그인이 필요합니다."}, 401


def redirect_to_login():
    return redirect(url_for("auth.page_sign_in"))