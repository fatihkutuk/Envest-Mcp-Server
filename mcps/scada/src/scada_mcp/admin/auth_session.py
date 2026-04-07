import bcrypt
import secrets
import time

_sessions: dict[str, dict] = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_session(username: str, role: str, max_age: int = 86400) -> str:
    token = secrets.token_hex(32)
    _sessions[token] = {
        "username": username,
        "role": role,
        "created_at": time.time(),
        "expires_at": time.time() + max_age,
    }
    return token


def get_session(token: str) -> dict | None:
    s = _sessions.get(token)
    if s and s["expires_at"] > time.time():
        return s
    if s:
        del _sessions[token]
    return None


def destroy_session(token: str):
    _sessions.pop(token, None)


def get_session_from_request(request) -> dict | None:
    cookie = request.cookies.get("admin_session")
    if cookie:
        return get_session(cookie)
    return None
