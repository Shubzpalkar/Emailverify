import os
import uuid
from datetime import datetime, timezone
from database import get_db
from schemas.profile import (
    FullProfileResponse, PersonalInfoResponse, WorkspaceInfoResponse,
    UserPreferencesResponse, AccountMetadataResponse, PersonalInfoUpdate,
    UserPreferencesUpdate, SessionResponse, LoginHistoryResponse
)

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "avatars")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def _log_audit(db, user_id: str, action: str, details: str, workspace_id: str = None):
    try:
        if not workspace_id:
            row = db.execute("SELECT workspace_id FROM users WHERE id = ?", [user_id]).fetchone()
            workspace_id = row[0] if row and row[0] else user_id

        db.execute("""
            INSERT INTO audit_logs (id, workspace_id, actor_id, action, target_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [str(uuid.uuid4()), workspace_id, user_id, action, user_id, details, datetime.now(timezone.utc)])
    except Exception as e:
        print(f"[AUDIT LOG ERROR] {e}", flush=True)


def parse_user_agent(ua_string: str) -> tuple[str, str]:
    if not ua_string:
        return ("Unknown Browser", "Unknown Device")
    
    ua = ua_string.lower()
    browser = "Unknown Browser"
    if "chrome" in ua and "edg" not in ua:
        browser = "Google Chrome"
    elif "edg" in ua:
        browser = "Microsoft Edge"
    elif "firefox" in ua:
        browser = "Mozilla Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Apple Safari"
    elif "opera" in ua or "opr" in ua:
        browser = "Opera"

    device = "Desktop"
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        device = "Mobile"
    elif "ipad" in ua or "tablet" in ua:
        device = "Tablet"

    return (browser, device)


def get_user_preferences_internal(db, user_id: str) -> UserPreferencesResponse:
    row = db.execute("""
        SELECT theme, email_notifications, notify_verification_completed,
               notify_credit_alerts, notify_team_invites, notify_security_alerts,
               download_preference, verification_preference, updated_at
        FROM user_preferences
        WHERE user_id = ?
    """, [user_id]).fetchone()

    if not row:
        now = datetime.now(timezone.utc)
        db.execute("""
            INSERT INTO user_preferences (user_id, theme, email_notifications, notify_verification_completed,
                                          notify_credit_alerts, notify_team_invites, notify_security_alerts,
                                          download_preference, verification_preference, updated_at)
            VALUES (?, 'system', TRUE, TRUE, TRUE, TRUE, TRUE, 'CSV', 'standard', ?)
        """, [user_id, now])
        return UserPreferencesResponse(
            theme="system",
            email_notifications=True,
            notify_verification_completed=True,
            notify_credit_alerts=True,
            notify_team_invites=True,
            notify_security_alerts=True,
            download_preference="CSV",
            verification_preference="standard",
            updated_at=now
        )

    return UserPreferencesResponse(
        theme=row[0] or "system",
        email_notifications=bool(row[1]),
        notify_verification_completed=bool(row[2]),
        notify_credit_alerts=bool(row[3]),
        notify_team_invites=bool(row[4]),
        notify_security_alerts=bool(row[5]),
        download_preference=row[6] or "CSV",
        verification_preference=row[7] or "standard",
        updated_at=row[8]
    )


def get_full_profile(user_id: str) -> FullProfileResponse:
    db = get_db()
    user_row = db.execute("""
        SELECT id, firebase_uid, email, display_name, role, plan, status, created_at, last_login,
               email_verified, phone, workspace_id, department, job_title, employee_id, timezone,
               language, avatar_url, password_last_changed, updated_at, joined_at
        FROM users
        WHERE id = ?
    """, [user_id]).fetchone()

    if not user_row:
        raise ValueError("User not found")

    ws_info = WorkspaceInfoResponse(
        company_name="My Workspace",
        workspace_name="Default Workspace",
        current_role=user_row[4] or "user",
        workspace_plan=user_row[5] or "Free",
        date_joined=user_row[20] or user_row[7],
        workspace_status="Active"
    )

    if user_row[11]: # workspace_id
        ws_row = db.execute("""
            SELECT company_name, workspace_slug, plan, workspace_status
            FROM workspaces
            WHERE id = ?
        """, [user_row[11]]).fetchone()
        if ws_row:
            ws_info.company_name = ws_row[0] or "My Workspace"
            ws_info.workspace_name = ws_row[1] or "Default Workspace"
            ws_info.workspace_plan = ws_row[2] or user_row[5] or "Free"
            ws_info.workspace_status = ws_row[3] or "Active"

    personal_info = PersonalInfoResponse(
        id=user_row[0],
        display_name=user_row[3],
        email=user_row[2],
        phone=user_row[10],
        job_title=user_row[13],
        department=user_row[12],
        employee_id=user_row[14],
        timezone=user_row[15] or "UTC",
        language=user_row[16] or "en",
        avatar_url=user_row[17]
    )

    preferences = get_user_preferences_internal(db, user_id)

    account_meta = AccountMetadataResponse(
        user_id=user_row[0],
        firebase_uid=user_row[1],
        created_at=user_row[7],
        last_login=user_row[8],
        updated_at=user_row[19] or user_row[7],
        account_status=user_row[6] or "Active",
        email_verified=bool(user_row[9]),
        password_last_changed=user_row[18]
    )

    return FullProfileResponse(
        personal_info=personal_info,
        workspace_info=ws_info,
        preferences=preferences,
        account_metadata=account_meta
    )


def update_personal_profile(user_id: str, data: PersonalInfoUpdate) -> PersonalInfoResponse:
    db = get_db()
    now = datetime.now(timezone.utc)

    db.execute("""
        UPDATE users
        SET display_name = COALESCE(?, display_name),
            phone = COALESCE(?, phone),
            job_title = COALESCE(?, job_title),
            department = COALESCE(?, department),
            employee_id = COALESCE(?, employee_id),
            timezone = COALESCE(?, timezone),
            language = COALESCE(?, language),
            updated_at = ?
        WHERE id = ?
    """, [
        data.display_name,
        data.phone,
        data.job_title,
        data.department,
        data.employee_id,
        data.timezone,
        data.language,
        now,
        user_id
    ])

    _log_audit(db, user_id, "Profile Updated", f"Updated personal profile for {user_id}")

    profile = get_full_profile(user_id)
    return profile.personal_info


def save_user_avatar(user_id: str, file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        raise ValueError("Unsupported image format. Allowed: JPG, JPEG, PNG, WEBP")

    if len(file_bytes) > 2 * 1024 * 1024:
        raise ValueError("Image file size exceeds maximum limit of 2MB")

    avatar_filename = f"avatar_{user_id}{ext}"
    file_path = os.path.join(UPLOADS_DIR, avatar_filename)

    # Optional PIL resizing if Pillow available
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(file_bytes))
        img.thumbnail((300, 300))
        img.save(file_path)
    except Exception:
        with open(file_path, "wb") as f:
            f.write(file_bytes)

    avatar_url = f"/uploads/avatars/{avatar_filename}"
    db = get_db()
    now = datetime.now(timezone.utc)
    db.execute("UPDATE users SET avatar_url = ?, updated_at = ? WHERE id = ?", [avatar_url, now, user_id])

    _log_audit(db, user_id, "Avatar Changed", f"Uploaded new profile avatar: {avatar_filename}")

    return avatar_url


def update_user_preferences(user_id: str, data: UserPreferencesUpdate) -> UserPreferencesResponse:
    db = get_db()
    now = datetime.now(timezone.utc)

    existing = db.execute("SELECT user_id FROM user_preferences WHERE user_id = ?", [user_id]).fetchone()
    if existing:
        db.execute("""
            UPDATE user_preferences
            SET theme = COALESCE(?, theme),
                email_notifications = COALESCE(?, email_notifications),
                notify_verification_completed = COALESCE(?, notify_verification_completed),
                notify_credit_alerts = COALESCE(?, notify_credit_alerts),
                notify_team_invites = COALESCE(?, notify_team_invites),
                notify_security_alerts = COALESCE(?, notify_security_alerts),
                download_preference = COALESCE(?, download_preference),
                verification_preference = COALESCE(?, verification_preference),
                updated_at = ?
            WHERE user_id = ?
        """, [
            data.theme,
            data.email_notifications,
            data.notify_verification_completed,
            data.notify_credit_alerts,
            data.notify_team_invites,
            data.notify_security_alerts,
            data.download_preference,
            data.verification_preference,
            now,
            user_id
        ])
    else:
        db.execute("""
            INSERT INTO user_preferences (user_id, theme, email_notifications, notify_verification_completed,
                                          notify_credit_alerts, notify_team_invites, notify_security_alerts,
                                          download_preference, verification_preference, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            user_id,
            data.theme or "system",
            data.email_notifications if data.email_notifications is not None else True,
            data.notify_verification_completed if data.notify_verification_completed is not None else True,
            data.notify_credit_alerts if data.notify_credit_alerts is not None else True,
            data.notify_team_invites if data.notify_team_invites is not None else True,
            data.notify_security_alerts if data.notify_security_alerts is not None else True,
            data.download_preference or "CSV",
            data.verification_preference or "standard",
            now
        ])

    _log_audit(db, user_id, "Preferences Changed", "Updated user application & notification preferences")

    return get_user_preferences_internal(db, user_id)


def get_active_sessions(user_id: str, current_ip: str = "127.0.0.1", user_agent: str = "") -> list[SessionResponse]:
    db = get_db()
    rows = db.execute("""
        SELECT id, browser, device, ip_address, location, login_time, last_activity, is_current
        FROM user_sessions
        WHERE user_id = ?
        ORDER BY last_activity DESC
    """, [user_id]).fetchall()

    if not rows:
        # Create initial active session if none exists
        browser, device = parse_user_agent(user_agent)
        sess_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        db.execute("""
            INSERT INTO user_sessions (id, user_id, session_token, browser, device, ip_address, location, login_time, last_activity, is_current)
            VALUES (?, ?, ?, ?, ?, ?, 'Local Workspace', ?, ?, TRUE)
        """, [sess_id, user_id, sess_id, browser, device, current_ip, now, now])
        rows = [(sess_id, browser, device, current_ip, "Local Workspace", now, now, True)]

    sessions = []
    for r in rows:
        sessions.append(SessionResponse(
            id=r[0],
            browser=r[1] or "Google Chrome",
            device=r[2] or "Desktop",
            ip_address=r[3] or "127.0.0.1",
            location=r[4] or "Local Workspace",
            login_time=r[5],
            last_activity=r[6],
            is_current=bool(r[7])
        ))
    return sessions


def revoke_session(user_id: str, session_id: str) -> bool:
    db = get_db()
    row = db.execute("SELECT is_current FROM user_sessions WHERE id = ? AND user_id = ?", [session_id, user_id]).fetchone()
    if not row:
        raise ValueError("Session not found")
    if bool(row[0]):
        raise ValueError("Cannot revoke your current active session")

    db.execute("DELETE FROM user_sessions WHERE id = ? AND user_id = ?", [session_id, user_id])
    _log_audit(db, user_id, "Session Revoked", f"Revoked active session {session_id}")
    return True


def get_user_login_history(user_id: str) -> list[LoginHistoryResponse]:
    db = get_db()
    rows = db.execute("""
        SELECT id, login_time, browser, device, ip_address, location, status
        FROM login_history
        WHERE user_id = ?
        ORDER BY login_time DESC
        LIMIT 20
    """, [user_id]).fetchall()

    if not rows:
        # Seed an initial record if empty
        now = datetime.now(timezone.utc)
        hist_id = str(uuid.uuid4())
        db.execute("""
            INSERT INTO login_history (id, user_id, login_time, browser, device, ip_address, location, status)
            VALUES (?, ?, ?, 'Google Chrome', 'Desktop', '127.0.0.1', 'Local Workspace', 'Success')
        """, [hist_id, user_id, now])
        rows = [(hist_id, now, "Google Chrome", "Desktop", "127.0.0.1", "Local Workspace", "Success")]

    history = []
    for r in rows:
        history.append(LoginHistoryResponse(
            id=r[0],
            login_time=r[1],
            browser=r[2] or "Google Chrome",
            device=r[3] or "Desktop",
            ip_address=r[4] or "127.0.0.1",
            location=r[5] or "Local Workspace",
            status=r[6] or "Success"
        ))
    return history


def record_password_changed(user_id: str):
    db = get_db()
    now = datetime.now(timezone.utc)
    db.execute("UPDATE users SET password_last_changed = ?, updated_at = ? WHERE id = ?", [now, now, user_id])
    _log_audit(db, user_id, "Password Changed", "User updated password securely")
    return {"status": "success", "password_last_changed": now}
