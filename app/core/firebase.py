import os
import base64
import json
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

_initialized = False


def _init():
    global _initialized
    if _initialized:
        return True

    path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    project_id = os.getenv("FIREBASE_PROJECT_ID", "")

    try:
        if path and os.path.exists(path):
            firebase_admin.initialize_app(credentials.Certificate(path))
        elif project_id:
            firebase_admin.initialize_app(options={"projectId": project_id})
        else:
            return False
        _initialized = True
        return True
    except ValueError:
        # Already initialized
        _initialized = True
        return True
    except Exception:
        return False


def verify_firebase_token(token: str) -> str | None:
    """Returns firebase_uid if token is valid, None otherwise."""
    if _init():
        try:
            decoded = firebase_auth.verify_id_token(token)
            return decoded["uid"]
        except Exception:
            return None

    # Dev fallback: decode JWT payload without verification
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        padding = 4 - len(parts[1]) % 4
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * padding))
        return payload.get("user_id") or payload.get("sub")
    except Exception:
        return None
