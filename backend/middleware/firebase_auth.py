from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_admin_auth

from firebase.firebase import initialize_firebase

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
    initialize_firebase()

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
        decoded = firebase_admin_auth.verify_id_token(token, check_revoked=True, clock_skew_seconds=60)
    except firebase_admin_auth.RevokedIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    except firebase_admin_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except firebase_admin_auth.UserDisabledError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User disabled")
    except Exception as e:
        print(f"[AUTH ERROR] Firebase token verification failed: {e}", flush=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")


    uid = decoded.get("uid")
    email = decoded.get("email")
    if not uid or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return FirebaseUser(
        firebase_uid=uid,
        email=email,
        display_name=decoded.get("name"),
        email_verified=bool(decoded.get("email_verified", False)),
    )
