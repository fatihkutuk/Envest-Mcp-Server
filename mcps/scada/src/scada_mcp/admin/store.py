from __future__ import annotations

import json
import logging
import secrets
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..auth import mint_token
from .auth_session import hash_password

logger = logging.getLogger(__name__)


class DataStore:
    """JSON file-based storage for admin users and API tokens.

    Thread-safe: every public method acquires the internal lock before
    reading or writing files.
    """

    def __init__(self, data_dir: str | Path) -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._users_path = self._data_dir / "users.json"
        self._tokens_path = self._data_dir / "tokens.json"
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def load_users(self) -> list[dict]:
        with self._lock:
            return self._read_json(self._users_path, [])

    def save_users(self, users: list[dict]) -> None:
        with self._lock:
            self._write_json(self._users_path, users)

    def get_user(self, username: str) -> dict | None:
        with self._lock:
            users = self._read_json(self._users_path, [])
            return next((u for u in users if u["username"] == username), None)

    def create_user(self, username: str, password: str, role: str) -> dict:
        with self._lock:
            users = self._read_json(self._users_path, [])
            if any(u["username"] == username for u in users):
                raise ValueError(f"User '{username}' already exists")
            user = {
                "username": username,
                "password_hash": hash_password(password),
                "role": role,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            users.append(user)
            self._write_json(self._users_path, users)
            return user

    def update_user_password(self, username: str, new_password: str) -> bool:
        with self._lock:
            users = self._read_json(self._users_path, [])
            for user in users:
                if user["username"] == username:
                    user["password_hash"] = hash_password(new_password)
                    self._write_json(self._users_path, users)
                    return True
            return False

    def update_user_role(self, username: str, new_role: str) -> bool:
        with self._lock:
            users = self._read_json(self._users_path, [])
            for user in users:
                if user["username"] == username:
                    # Refuse to remove admin from last admin
                    if user.get("role") == "admin" and new_role != "admin":
                        admin_count = sum(1 for u in users if u.get("role") == "admin")
                        if admin_count <= 1:
                            raise ValueError("Cannot change role of the last admin user")
                    user["role"] = new_role
                    self._write_json(self._users_path, users)
                    return True
            return False

    def delete_user(self, username: str) -> bool:
        with self._lock:
            users = self._read_json(self._users_path, [])
            target = next((u for u in users if u["username"] == username), None)
            if target is None:
                return False
            # Refuse to delete the last admin
            if target.get("role") == "admin":
                admin_count = sum(1 for u in users if u.get("role") == "admin")
                if admin_count <= 1:
                    raise ValueError("Cannot delete the last admin user")
            users = [u for u in users if u["username"] != username]
            self._write_json(self._users_path, users)
            return True

    def ensure_default_admin(self) -> None:
        """Create a default admin/admin account if no users exist.

        Logs a warning so operators know to change the password.
        """
        with self._lock:
            users = self._read_json(self._users_path, [])
            if users:
                return
            logger.warning(
                "No users found -- creating default admin account "
                "(username='admin', password='admin'). "
                "Change this password immediately!"
            )
            user = {
                "username": "admin",
                "password_hash": hash_password("admin"),
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write_json(self._users_path, [user])

    # ------------------------------------------------------------------
    # Tokens
    # ------------------------------------------------------------------

    def load_tokens(self) -> list[dict]:
        with self._lock:
            return self._read_json(self._tokens_path, [])

    def save_tokens(self, tokens: list[dict]) -> None:
        with self._lock:
            self._write_json(self._tokens_path, tokens)

    def get_token(self, token_id: str) -> dict | None:
        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            return next((t for t in tokens if t["token_id"] == token_id), None)

    def create_token(
        self,
        name: str,
        allowed_instances: list[str],
        created_by: str,
        expires_at: str | None = None,
    ) -> tuple[dict, str]:
        """Create a new API token.

        Returns a tuple of (stored record, JWT string).  The JWT is also
        persisted in the token record so it can be displayed later.
        """
        token_id = "tok_" + secrets.token_hex(16)
        token_secret = secrets.token_hex(32)

        # Compute TTL for mint_token
        if expires_at:
            exp_dt = datetime.fromisoformat(expires_at)
            now_dt = datetime.now(timezone.utc)
            ttl_sec = max(0, int((exp_dt - now_dt).total_seconds()))
        else:
            ttl_sec = 0  # long-lived

        jwt_string = mint_token(
            token_secret=token_secret,
            sub=token_id,
            ttl_sec=ttl_sec,
        )

        record = {
            "token_id": token_id,
            "name": name,
            "token_secret": token_secret,
            "jwt": jwt_string,
            "allowed_instances": allowed_instances,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "revoked": False,
        }

        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            tokens.append(record)
            self._write_json(self._tokens_path, tokens)

        return record, jwt_string

    def get_token_jwt(self, token_id: str) -> str | None:
        """Return the stored JWT string for a token, or None."""
        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            tok = next((t for t in tokens if t["token_id"] == token_id), None)
            if tok is None:
                return None
            return tok.get("jwt")

    _SENTINEL = object()

    def update_token(
        self,
        token_id: str,
        *,
        name: str | None = None,
        allowed_instances: list[str] | None = None,
        expires_at: str | None | object = _SENTINEL,
    ) -> bool:
        """Update mutable fields of a token record.

        ``expires_at`` uses a sentinel default so that passing ``None``
        explicitly clears the expiry, while omitting it leaves it unchanged.
        """
        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            for token in tokens:
                if token["token_id"] == token_id:
                    if name is not None:
                        token["name"] = name
                    if allowed_instances is not None:
                        token["allowed_instances"] = allowed_instances
                    if expires_at is not self._SENTINEL:
                        token["expires_at"] = expires_at
                    self._write_json(self._tokens_path, tokens)
                    return True
            return False

    def revoke_token(self, token_id: str) -> bool:
        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            for token in tokens:
                if token["token_id"] == token_id:
                    token["revoked"] = True
                    self._write_json(self._tokens_path, tokens)
                    return True
            return False

    def delete_token(self, token_id: str) -> bool:
        """Permanently delete a token from storage."""
        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            before = len(tokens)
            tokens = [t for t in tokens if t["token_id"] != token_id]
            if len(tokens) < before:
                self._write_json(self._tokens_path, tokens)
                return True
            return False

    def get_active_tokens(self) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            return [
                t
                for t in tokens
                if not t.get("revoked")
                and (t.get("expires_at") is None or t["expires_at"] > now)
            ]

    def get_tokens_for_instance(self, instance_id: str) -> list[dict]:
        with self._lock:
            tokens = self._read_json(self._tokens_path, [])
            return [
                t
                for t in tokens
                if instance_id in t.get("allowed_instances", [])
            ]

    # ------------------------------------------------------------------
    # Internal helpers (caller must hold self._lock)
    # ------------------------------------------------------------------

    @staticmethod
    def _read_json(path: Path, default):
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _write_json(path: Path, data) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
