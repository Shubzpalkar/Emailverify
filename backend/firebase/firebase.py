import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)

_FIREBASE_APP = None


def initialize_firebase():
    """Initialize Firebase Admin once and return the app instance."""
    global _FIREBASE_APP

    if _FIREBASE_APP:
        return _FIREBASE_APP

    if firebase_admin._apps:
        _FIREBASE_APP = firebase_admin.get_app()
        return _FIREBASE_APP

    firebase_dir = Path(__file__).resolve().parent
    key_path = firebase_dir / "firebase-key.json"
    if not key_path.exists():
        fallback_path = firebase_dir / "firebase-key.json.json"
        if fallback_path.exists():
            key_path = fallback_path

    if not key_path.exists():
        raise FileNotFoundError(f"Firebase service account key not found at {key_path}")

    cred = credentials.Certificate(str(key_path))
    _FIREBASE_APP = firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized")
    return _FIREBASE_APP
