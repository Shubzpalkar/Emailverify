import os
import json
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

    # Check env var for raw JSON string
    env_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if env_json:
        try:
            cred_dict = json.loads(env_json)
            cred = credentials.Certificate(cred_dict)
            _FIREBASE_APP = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized from JSON environment variable")
            return _FIREBASE_APP
        except Exception as e:
            logger.error(f"Failed to initialize Firebase from FIREBASE_CREDENTIALS_JSON: {e}")

    # Check env var for custom path
    env_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if env_path and Path(env_path).exists():
        cred = credentials.Certificate(env_path)
        _FIREBASE_APP = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized from path specified in environment")
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
