import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_admin_auth
import google.oauth2.id_token
import google.auth.transport.requests

from firebase.firebase import initialize_firebase
from starlette.concurrency import run_in_threadpool

from config import settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class FirebaseUser:
    firebase_uid: str
    email: str
    display_name: Optional[str]
    email_verified: bool
    disabled: bool = False


async def verify_firebase_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> FirebaseUser:
    app = initialize_firebase()

    token = credentials.credentials if credentials else None
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization bearer token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decoded = await run_in_threadpool(
            firebase_admin_auth.verify_id_token,
            token,
            check_revoked=False,
            clock_skew_seconds=min(getattr(settings, "FIREBASE_CLOCK_SKEW_SECONDS", 60), 60)
        )
    except firebase_admin_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    except firebase_admin_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except firebase_admin_auth.UserDisabledError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")
    except Exception as e:
        error_str = str(e)
        if "used too early" in error_str or "clock" in error_str or "future" in error_str:
            print(f"[AUTH WARNING] Clock skew detected ({error_str}), attempting fallback verification with 300s window...", flush=True)
            try:
                req_adapter = google.auth.transport.requests.Request()
                project_id = getattr(app, "project_id", None) or "email-verifier-4761a"
                decoded = await run_in_threadpool(
                    google.oauth2.id_token.verify_firebase_token,
                    token,
                    req_adapter,
                    audience=project_id,
                    clock_skew_in_seconds=300
                )
            except Exception as fallback_err:
                print(f"[AUTH ERROR] Fallback token verification failed: {fallback_err}", flush=True)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {error_str}")
        else:
            print(f"[AUTH ERROR] Firebase token verification failed: {e}", flush=True)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {error_str}")

    uid = decoded.get("uid") or decoded.get("sub")
    email = decoded.get("email")
    if not uid or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return FirebaseUser(
        firebase_uid=uid,
        email=email,
        display_name=decoded.get("name"),
        email_verified=bool(decoded.get("email_verified", False)),
    )

