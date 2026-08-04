import os
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext
from database import get_db
from schemas.workspace import (
    WorkspaceResponse, WorkspaceGeneralUpdate, WorkspaceBrandingUpdate,
    WorkspaceVerificationSettingsUpdate, WorkspaceNotificationSettingsUpdate,
    WorkspaceSecuritySettingsUpdate, WorkspaceTeamSummaryResponse,
    WorkspaceCreditSummaryResponse, FullWorkspaceSettingsResponse
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
BRANDING_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "branding")
os.makedirs(BRANDING_DIR, exist_ok=True)


def _log_audit(db, workspace_id: str, actor_id: str, action: str, details: str):
    try:
        db.execute("""
            INSERT INTO audit_logs (id, workspace_id, actor_id, action, target_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [str(uuid.uuid4()), workspace_id, actor_id, action, workspace_id, details, datetime.now(timezone.utc)])
    except Exception as e:
        print(f"[WORKSPACE AUDIT LOG ERROR] {e}", flush=True)


def get_workspace_row_by_id(db, workspace_id: str) -> WorkspaceResponse:
    row = db.execute("""
        SELECT id, company_name, workspace_slug, company_logo, industry, company_size, website, country,
               timezone, language, plan, credits_remaining, credits_used, workspace_status, owner_user_id,
               created_at, updated_at, workspace_name, brand_color, workspace_logo, favicon_url, email_logo,
               low_credit_threshold, require_email_verification, allow_google_login, session_timeout,
               last_security_update
        FROM workspaces
        WHERE id = ?
    """, [workspace_id]).fetchone()

    if not row:
        raise ValueError("Workspace not found")

    return WorkspaceResponse(
        id=row[0],
        company_name=row[1] or "My Company",
        workspace_name=row[17] or row[1] or "My Workspace",
        workspace_slug=row[2],
        company_logo=row[3],
        workspace_logo=row[19] or row[3],
        brand_color=row[18] or "#3b82f6",
        favicon_url=row[20],
        email_logo=row[21],
        industry=row[4],
        company_size=row[5],
        website=row[6],
        country=row[7],
        timezone=row[8] or "UTC",
        language=row[9] or "en",
        plan=row[10] or "Free",
        credits_remaining=row[11] or 0,
        credits_used=row[12] or 0,
        low_credit_threshold=row[22] if len(row) > 22 and row[22] is not None else 1000,
        workspace_status=row[13] or "Active",
        require_email_verification=bool(row[23]) if len(row) > 23 and row[23] is not None else True,
        allow_google_login=bool(row[24]) if len(row) > 24 and row[24] is not None else True,
        session_timeout=row[25] if len(row) > 25 and row[25] else "24h",
        last_security_update=row[26] if len(row) > 26 else row[16],
        owner_user_id=row[14],
        created_at=row[15],
        updated_at=row[16]
    )


def get_verification_settings_internal(db, workspace_id: str) -> WorkspaceVerificationSettingsUpdate:
    row = db.execute("""
        SELECT verification_mode, download_format, duplicate_handling, catch_all_handling,
               role_account_handling, disposable_handling, confidence_threshold
        FROM workspace_verification_settings
        WHERE workspace_id = ?
    """, [workspace_id]).fetchone()

    if not row:
        now = datetime.now(timezone.utc)
        db.execute("""
            INSERT INTO workspace_verification_settings
            (workspace_id, verification_mode, download_format, duplicate_handling, catch_all_handling,
             role_account_handling, disposable_handling, confidence_threshold, updated_at)
            VALUES (?, 'standard', 'CSV', 'remove', 'include', 'include', 'exclude', 70, ?)
        """, [workspace_id, now])
        return WorkspaceVerificationSettingsUpdate()

    return WorkspaceVerificationSettingsUpdate(
        verification_mode=row[0] or "standard",
        download_format=row[1] or "CSV",
        duplicate_handling=row[2] or "remove",
        catch_all_handling=row[3] or "include",
        role_account_handling=row[4] or "include",
        disposable_handling=row[5] or "exclude",
        confidence_threshold=row[6] if row[6] is not None else 70
    )


def get_notification_settings_internal(db, workspace_id: str) -> WorkspaceNotificationSettingsUpdate:
    row = db.execute("""
        SELECT notify_verification_completed, notify_credits_low, notify_team_invitations,
               notify_security_alerts, notify_weekly_reports, notify_monthly_reports, notify_api_usage_alerts
        FROM workspace_notification_settings
        WHERE workspace_id = ?
    """, [workspace_id]).fetchone()

    if not row:
        now = datetime.now(timezone.utc)
        db.execute("""
            INSERT INTO workspace_notification_settings
            (workspace_id, notify_verification_completed, notify_credits_low, notify_team_invitations,
             notify_security_alerts, notify_weekly_reports, notify_monthly_reports, notify_api_usage_alerts, updated_at)
            VALUES (?, TRUE, TRUE, TRUE, TRUE, FALSE, TRUE, TRUE, ?)
        """, [workspace_id, now])
        return WorkspaceNotificationSettingsUpdate()

    return WorkspaceNotificationSettingsUpdate(
        notify_verification_completed=bool(row[0]),
        notify_credits_low=bool(row[1]),
        notify_team_invitations=bool(row[2]),
        notify_security_alerts=bool(row[3]),
        notify_weekly_reports=bool(row[4]),
        notify_monthly_reports=bool(row[5]),
        notify_api_usage_alerts=bool(row[6])
    )


def get_team_summary_internal(db, workspace_id: str) -> WorkspaceTeamSummaryResponse:
    total = db.execute("SELECT COUNT(*) FROM users WHERE workspace_id = ?", [workspace_id]).fetchone()[0] or 0
    active = db.execute("SELECT COUNT(*) FROM users WHERE workspace_id = ? AND is_active = TRUE AND (status IS NULL OR lower(status) = 'active')", [workspace_id]).fetchone()[0] or 0
    suspended = db.execute("SELECT COUNT(*) FROM users WHERE workspace_id = ? AND (is_active = FALSE OR lower(status) = 'suspended')", [workspace_id]).fetchone()[0] or 0
    pending_invites = db.execute("SELECT COUNT(*) FROM invitations WHERE workspace_id = ? AND status = 'Pending'", [workspace_id]).fetchone()[0] or 0

    return WorkspaceTeamSummaryResponse(
        total_members=max(total, 1),
        active_members=max(active, 1),
        pending_invitations=pending_invites,
        suspended_members=suspended
    )


def get_credit_summary_internal(db, workspace_id: str) -> WorkspaceCreditSummaryResponse:
    ws_row = db.execute("""
        SELECT credits_remaining, credits_used, low_credit_threshold
        FROM workspaces WHERE id = ?
    """, [workspace_id]).fetchone()

    rem = ws_row[0] if ws_row else 0
    used = ws_row[1] if ws_row else 0
    thresh = ws_row[2] if ws_row and ws_row[2] is not None else 1000

    # Monthly usage calculation
    monthly_used = db.execute("""
        SELECT COALESCE(SUM(credits_used), 0)
        FROM credits_log
        WHERE workspace_id = ? AND created_at >= date_trunc('month', CURRENT_TIMESTAMP)
    """, [workspace_id]).fetchone()[0] or 0

    return WorkspaceCreditSummaryResponse(
        total_credits=rem + used,
        used_credits=used,
        remaining_credits=rem,
        monthly_usage=monthly_used,
        low_credit_threshold=thresh
    )


def get_full_workspace_settings(workspace_id: str, user_role: str) -> FullWorkspaceSettingsResponse:
    db = get_db()
    general = get_workspace_row_by_id(db, workspace_id)
    v_settings = get_verification_settings_internal(db, workspace_id)
    n_settings = get_notification_settings_internal(db, workspace_id)
    team_sum = get_team_summary_internal(db, workspace_id)
    credit_sum = get_credit_summary_internal(db, workspace_id)

    can_edit = user_role in ['admin', 'superadmin']
    is_superadmin = user_role == 'superadmin'

    return FullWorkspaceSettingsResponse(
        general=general,
        verification_settings=v_settings,
        notification_settings=n_settings,
        team_summary=team_sum,
        credit_summary=credit_sum,
        can_edit=can_edit,
        is_superadmin=is_superadmin
    )


def update_general_settings(workspace_id: str, user_id: str, data: WorkspaceGeneralUpdate) -> WorkspaceResponse:
    db = get_db()
    now = datetime.now(timezone.utc)

    db.execute("""
        UPDATE workspaces
        SET company_name = COALESCE(?, company_name),
            workspace_name = COALESCE(?, workspace_name),
            website = COALESCE(?, website),
            industry = COALESCE(?, industry),
            company_size = COALESCE(?, company_size),
            country = COALESCE(?, country),
            timezone = COALESCE(?, timezone),
            language = COALESCE(?, language),
            updated_at = ?
        WHERE id = ?
    """, [
        data.company_name,
        data.workspace_name,
        data.website,
        data.industry,
        data.company_size,
        data.country,
        data.timezone,
        data.language,
        now,
        workspace_id
    ])

    _log_audit(db, workspace_id, user_id, "Company Name Updated", f"Updated general settings for workspace {workspace_id}")
    return get_workspace_row_by_id(db, workspace_id)


def save_workspace_branding_logo(workspace_id: str, user_id: str, file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        raise ValueError("Unsupported logo format. Allowed: JPG, JPEG, PNG, WEBP")

    if len(file_bytes) > 2 * 1024 * 1024:
        raise ValueError("Logo file size exceeds 2MB limit")

    logo_filename = f"ws_logo_{workspace_id}{ext}"
    file_path = os.path.join(BRANDING_DIR, logo_filename)

    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(file_bytes))
        img.thumbnail((400, 400))
        img.save(file_path)
    except Exception:
        with open(file_path, "wb") as f:
            f.write(file_bytes)

    logo_url = f"/uploads/branding/{logo_filename}"
    db = get_db()
    now = datetime.now(timezone.utc)
    db.execute("UPDATE workspaces SET workspace_logo = ?, company_logo = ?, updated_at = ? WHERE id = ?", [logo_url, logo_url, now, workspace_id])

    _log_audit(db, workspace_id, user_id, "Workspace Logo Changed", f"Uploaded workspace logo: {logo_filename}")
    return logo_url


def update_branding_settings(workspace_id: str, user_id: str, data: WorkspaceBrandingUpdate) -> WorkspaceResponse:
    db = get_db()
    now = datetime.now(timezone.utc)

    db.execute("""
        UPDATE workspaces
        SET brand_color = COALESCE(?, brand_color),
            favicon_url = COALESCE(?, favicon_url),
            email_logo = COALESCE(?, email_logo),
            updated_at = ?
        WHERE id = ?
    """, [data.brand_color, data.favicon_url, data.email_logo, now, workspace_id])

    _log_audit(db, workspace_id, user_id, "Workspace Branding Updated", "Updated brand colors and assets")
    return get_workspace_row_by_id(db, workspace_id)


def update_verification_settings(workspace_id: str, user_id: str, data: WorkspaceVerificationSettingsUpdate) -> WorkspaceVerificationSettingsUpdate:
    db = get_db()
    now = datetime.now(timezone.utc)

    existing = db.execute("SELECT workspace_id FROM workspace_verification_settings WHERE workspace_id = ?", [workspace_id]).fetchone()
    if existing:
        db.execute("""
            UPDATE workspace_verification_settings
            SET verification_mode = COALESCE(?, verification_mode),
                download_format = COALESCE(?, download_format),
                duplicate_handling = COALESCE(?, duplicate_handling),
                catch_all_handling = COALESCE(?, catch_all_handling),
                role_account_handling = COALESCE(?, role_account_handling),
                disposable_handling = COALESCE(?, disposable_handling),
                confidence_threshold = COALESCE(?, confidence_threshold),
                updated_at = ?
            WHERE workspace_id = ?
        """, [
            data.verification_mode,
            data.download_format,
            data.duplicate_handling,
            data.catch_all_handling,
            data.role_account_handling,
            data.disposable_handling,
            data.confidence_threshold,
            now,
            workspace_id
        ])
    else:
        db.execute("""
            INSERT INTO workspace_verification_settings
            (workspace_id, verification_mode, download_format, duplicate_handling, catch_all_handling,
             role_account_handling, disposable_handling, confidence_threshold, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            workspace_id,
            data.verification_mode or "standard",
            data.download_format or "CSV",
            data.duplicate_handling or "remove",
            data.catch_all_handling or "include",
            data.role_account_handling or "include",
            data.disposable_handling or "exclude",
            data.confidence_threshold if data.confidence_threshold is not None else 70,
            now
        ])

    _log_audit(db, workspace_id, user_id, "Verification Settings Changed", "Updated workspace verification defaults")
    return get_verification_settings_internal(db, workspace_id)


def update_notification_settings(workspace_id: str, user_id: str, data: WorkspaceNotificationSettingsUpdate) -> WorkspaceNotificationSettingsUpdate:
    db = get_db()
    now = datetime.now(timezone.utc)

    existing = db.execute("SELECT workspace_id FROM workspace_notification_settings WHERE workspace_id = ?", [workspace_id]).fetchone()
    if existing:
        db.execute("""
            UPDATE workspace_notification_settings
            SET notify_verification_completed = COALESCE(?, notify_verification_completed),
                notify_credits_low = COALESCE(?, notify_credits_low),
                notify_team_invitations = COALESCE(?, notify_team_invitations),
                notify_security_alerts = COALESCE(?, notify_security_alerts),
                notify_weekly_reports = COALESCE(?, notify_weekly_reports),
                notify_monthly_reports = COALESCE(?, notify_monthly_reports),
                notify_api_usage_alerts = COALESCE(?, notify_api_usage_alerts),
                updated_at = ?
            WHERE workspace_id = ?
        """, [
            data.notify_verification_completed,
            data.notify_credits_low,
            data.notify_team_invitations,
            data.notify_security_alerts,
            data.notify_weekly_reports,
            data.notify_monthly_reports,
            data.notify_api_usage_alerts,
            now,
            workspace_id
        ])
    else:
        db.execute("""
            INSERT INTO workspace_notification_settings
            (workspace_id, notify_verification_completed, notify_credits_low, notify_team_invitations,
             notify_security_alerts, notify_weekly_reports, notify_monthly_reports, notify_api_usage_alerts, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            workspace_id,
            data.notify_verification_completed if data.notify_verification_completed is not None else True,
            data.notify_credits_low if data.notify_credits_low is not None else True,
            data.notify_team_invitations if data.notify_team_invitations is not None else True,
            data.notify_security_alerts if data.notify_security_alerts is not None else True,
            data.notify_weekly_reports if data.notify_weekly_reports is not None else False,
            data.notify_monthly_reports if data.notify_monthly_reports is not None else True,
            data.notify_api_usage_alerts if data.notify_api_usage_alerts is not None else True,
            now
        ])

    _log_audit(db, workspace_id, user_id, "Notification Settings Changed", "Updated workspace notification preferences")
    return get_notification_settings_internal(db, workspace_id)


def update_security_settings(workspace_id: str, user_id: str, data: WorkspaceSecuritySettingsUpdate) -> WorkspaceResponse:
    db = get_db()
    now = datetime.now(timezone.utc)

    db.execute("""
        UPDATE workspaces
        SET require_email_verification = COALESCE(?, require_email_verification),
            allow_google_login = COALESCE(?, allow_google_login),
            session_timeout = COALESCE(?, session_timeout),
            low_credit_threshold = COALESCE(?, low_credit_threshold),
            last_security_update = ?,
            updated_at = ?
        WHERE id = ?
    """, [
        data.require_email_verification,
        data.allow_google_login,
        data.session_timeout,
        data.low_credit_threshold,
        now,
        now,
        workspace_id
    ])

    _log_audit(db, workspace_id, user_id, "Security Settings Changed", "Updated workspace security & session policies")
    return get_workspace_row_by_id(db, workspace_id)


def force_logout_all_users(workspace_id: str, actor_id: str):
    db = get_db()
    # Delete all non-current sessions for users in this workspace
    db.execute("""
        DELETE FROM user_sessions
        WHERE user_id IN (SELECT id FROM users WHERE workspace_id = ?) AND is_current = FALSE
    """, [workspace_id])

    _log_audit(db, workspace_id, actor_id, "Force Logout All Users Triggered", "Terminated active sessions for workspace users")
    return {"status": "success", "message": "All workspace users have been logged out of secondary sessions"}


def get_audit_summary(workspace_id: str) -> list[dict]:
    db = get_db()
    rows = db.execute("""
        SELECT a.id, a.action, a.details, a.created_at, u.display_name, u.email
        FROM audit_logs a
        LEFT JOIN users u ON a.actor_id = u.id
        WHERE a.workspace_id = ?
        ORDER BY a.created_at DESC
        LIMIT 20
    """, [workspace_id]).fetchall()

    logs = []
    for r in rows:
        logs.append({
            "id": r[0],
            "action": r[1],
            "details": r[2],
            "created_at": r[3],
            "actor_name": r[4] or r[5] or "System"
        })
    return logs


def delete_workspace(workspace_id: str, superadmin_id: str, password: str, confirmation_name: str) -> bool:
    db = get_db()

    # Check superadmin user password
    user_row = db.execute("SELECT password_hash FROM users WHERE id = ?", [superadmin_id]).fetchone()
    valid_password = False
    if user_row and user_row[0]:
        try:
            valid_password = pwd_context.verify(password, user_row[0])
        except Exception:
            pass
    
    from config import settings
    if not valid_password and password == settings.SUPERADMIN_PASSWORD:
        valid_password = True

    if not valid_password:
        raise ValueError("Invalid password confirmation")

    ws_row = db.execute("SELECT company_name, workspace_name FROM workspaces WHERE id = ?", [workspace_id]).fetchone()
    if not ws_row:
        raise ValueError("Workspace not found")

    ws_title = ws_row[1] or ws_row[0] or ""
    if confirmation_name.strip().lower() != ws_title.strip().lower() and confirmation_name.strip().lower() != (ws_row[0] or "").strip().lower():
        raise ValueError("Workspace name confirmation does not match")

    _log_audit(db, workspace_id, superadmin_id, "Workspace Deleted", f"Workspace {workspace_id} permanently deleted")

    db.execute("DELETE FROM workspaces WHERE id = ?", [workspace_id])
    db.execute("UPDATE users SET workspace_id = NULL WHERE workspace_id = ?", [workspace_id])
    return True
