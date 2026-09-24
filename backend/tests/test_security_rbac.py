import unittest
import os
import sys
import uuid
import duckdb
from datetime import datetime, timezone

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
# Point test database to isolated test database file
settings.DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_security.db")

from middleware.rbac import (
    ROLE_HIERARCHY, get_role_level, can_manage_role, can_assign_role
)
from auth import UserResponse
from routes.verify import _get_job_with_auth, _verify_job_ownership
from services import history_service, dashboard_service, analytics_service
from database import get_db, init_db


class TestRoleHierarchyAndPrivilegeEscalation(unittest.TestCase):
    """Test RBAC role hierarchy: viewer < user < manager < admin < superadmin"""

    def test_role_hierarchy_levels(self):
        self.assertEqual(get_role_level("viewer"), 1)
        self.assertEqual(get_role_level("user"), 2)
        self.assertEqual(get_role_level("manager"), 3)
        self.assertEqual(get_role_level("admin"), 4)
        self.assertEqual(get_role_level("superadmin"), 5)

        # Ensure strict ordering: viewer < user < manager < admin < superadmin
        self.assertLess(get_role_level("viewer"), get_role_level("user"))
        self.assertLess(get_role_level("user"), get_role_level("manager"))
        self.assertLess(get_role_level("manager"), get_role_level("admin"))
        self.assertLess(get_role_level("admin"), get_role_level("superadmin"))

    def test_prevent_escalation_to_superadmin(self):
        # Non-superadmins cannot assign superadmin role
        self.assertFalse(can_assign_role("admin", "superadmin"))
        self.assertFalse(can_assign_role("manager", "superadmin"))
        self.assertFalse(can_assign_role("user", "superadmin"))
        self.assertFalse(can_assign_role("viewer", "superadmin"))

    def test_manager_role_boundaries(self):
        # Manager can manage user and viewer
        self.assertTrue(can_manage_role("manager", "user"))
        self.assertTrue(can_manage_role("manager", "viewer"))

        # Manager CANNOT manage admin or another manager
        self.assertFalse(can_manage_role("manager", "admin"))
        self.assertFalse(can_manage_role("manager", "manager"))
        self.assertFalse(can_manage_role("manager", "superadmin"))

        # Manager can assign user and viewer
        self.assertTrue(can_assign_role("manager", "user"))
        self.assertTrue(can_assign_role("manager", "viewer"))

        # Manager CANNOT assign admin or superadmin
        self.assertFalse(can_assign_role("manager", "admin"))
        self.assertFalse(can_assign_role("manager", "superadmin"))

    def test_user_and_viewer_cannot_manage_or_assign(self):
        for actor in ["user", "viewer"]:
            for target in ["viewer", "user", "manager", "admin", "superadmin"]:
                self.assertFalse(can_manage_role(actor, target))
                self.assertFalse(can_assign_role(actor, target))

    def test_admin_workspace_scope(self):
        # Admin can manage workspace roles <= 4
        self.assertTrue(can_manage_role("admin", "admin"))
        self.assertTrue(can_manage_role("admin", "manager"))
        self.assertTrue(can_manage_role("admin", "user"))
        self.assertTrue(can_manage_role("admin", "viewer"))
        self.assertFalse(can_manage_role("admin", "superadmin"))

        # Admin can assign admin, manager, user, viewer
        self.assertTrue(can_assign_role("admin", "admin"))
        self.assertTrue(can_assign_role("admin", "manager"))
        self.assertTrue(can_assign_role("admin", "user"))
        self.assertTrue(can_assign_role("admin", "viewer"))
        self.assertFalse(can_assign_role("admin", "superadmin"))


class TestCrossTenantIsolation(unittest.TestCase):
    """Test strict tenant isolation for jobs, results, history, and invoices."""

    def setUp(self):
        init_db()
        self.db = get_db()
        self.ws_a = str(uuid.uuid4())
        self.ws_b = str(uuid.uuid4())
        self.user_a_id = str(uuid.uuid4())
        self.user_b_id = str(uuid.uuid4())

        self.email_a = f"a_{uuid.uuid4().hex[:8]}@tenant-a.com"
        self.email_b = f"b_{uuid.uuid4().hex[:8]}@tenant-b.com"

        # Create test workspaces
        self.db.execute("INSERT INTO workspaces (id, company_name, workspace_slug, owner_user_id) VALUES (?, 'Tenant A', ?, ?)", [self.ws_a, f"slug-{self.ws_a[:6]}", self.user_a_id])
        self.db.execute("INSERT INTO workspaces (id, company_name, workspace_slug, owner_user_id) VALUES (?, 'Tenant B', ?, ?)", [self.ws_b, f"slug-{self.ws_b[:6]}", self.user_b_id])

        # Create test users
        self.db.execute("INSERT INTO users (id, email, role, workspace_id, is_active, credit_pool) VALUES (?, ?, 'admin', ?, TRUE, 100)", [self.user_a_id, self.email_a, self.ws_a])
        self.db.execute("INSERT INTO users (id, email, role, workspace_id, is_active, credit_pool) VALUES (?, ?, 'admin', ?, TRUE, 100)", [self.user_b_id, self.email_b, self.ws_b])

        # Create job in Workspace A
        self.job_a_id = str(uuid.uuid4())
        self.db.execute("INSERT INTO verification_jobs (id, user_id, workspace_id, file_name, total_emails, status) VALUES (?, ?, ?, 'list_a.csv', 10, 'completed')", [self.job_a_id, self.user_a_id, self.ws_a])

        # Create invoice in Workspace A
        self.inv_a_id = str(uuid.uuid4())
        self.inv_number = f"INV-{uuid.uuid4().hex[:8]}"
        self.db.execute("INSERT INTO invoices (id, user_id, workspace_id, invoice_number, amount, plan_name, status) VALUES (?, ?, ?, ?, 999.0, 'Starter', 'paid')", [self.inv_a_id, self.user_a_id, self.ws_a, self.inv_number])

        self.user_a = UserResponse(
            id=self.user_a_id, email=self.email_a, role="admin", workspace_id=self.ws_a, is_active=True, credit_pool=100
        )
        self.user_b = UserResponse(
            id=self.user_b_id, email=self.email_b, role="admin", workspace_id=self.ws_b, is_active=True, credit_pool=100
        )

    def tearDown(self):
        try:
            self.db.execute("DELETE FROM invoices WHERE id = ?", [self.inv_a_id])
            self.db.execute("DELETE FROM verification_jobs WHERE id = ?", [self.job_a_id])
            self.db.execute("DELETE FROM users WHERE id IN (?, ?)", [self.user_a_id, self.user_b_id])
            self.db.execute("DELETE FROM workspaces WHERE id IN (?, ?)", [self.ws_a, self.ws_b])
        except Exception:
            pass

    def test_cross_tenant_job_access_blocked(self):
        # User A can access Job A
        job_a = _get_job_with_auth(self.db, self.job_a_id, self.user_a)
        self.assertIsNotNone(job_a)
        self.assertEqual(job_a[0], self.job_a_id)

        # User B (different workspace) CANNOT access Job A
        job_b_access = _get_job_with_auth(self.db, self.job_a_id, self.user_b)
        self.assertIsNone(job_b_access)

    def test_cross_tenant_history_details_blocked(self):
        # User A gets job details
        details = history_service.get_job_details(self.job_a_id, self.user_a.id, self.user_a.workspace_id, self.user_a.role)
        self.assertEqual(details["id"], self.job_a_id)

        # User B cannot get details for Job A
        with self.assertRaises(ValueError):
            history_service.get_job_details(self.job_a_id, self.user_b.id, self.user_b.workspace_id, self.user_b.role)

    def test_cross_tenant_timeline_blocked(self):
        # User B cannot access timeline of Job A
        with self.assertRaises(ValueError):
            history_service.get_job_timeline(self.job_a_id, self.user_b.id, self.user_b.workspace_id, self.user_b.role)

    def test_cross_tenant_diagnostics_blocked(self):
        # User B cannot access diagnostics of Job A
        with self.assertRaises(ValueError):
            history_service.get_job_diagnostics(self.job_a_id, self.user_b.id, self.user_b.workspace_id, self.user_b.role)


class TestNoFakeData(unittest.TestCase):
    """Test that all fake results and fake timeline/diagnostic data have been eliminated."""

    def setUp(self):
        init_db()
        self.db = get_db()
        self.ws_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.clean_email = f"clean_{uuid.uuid4().hex[:8]}@ws.com"
        self.db.execute("INSERT INTO workspaces (id, company_name, workspace_slug, owner_user_id) VALUES (?, 'Clean WS', ?, ?)", [self.ws_id, f"clean-{self.ws_id[:6]}", self.user_id])
        self.db.execute("INSERT INTO users (id, email, role, workspace_id, is_active, credit_pool) VALUES (?, ?, 'user', ?, TRUE, 100)", [self.user_id, self.clean_email, self.ws_id])

        self.empty_job_id = str(uuid.uuid4())
        self.db.execute("INSERT INTO verification_jobs (id, user_id, workspace_id, file_name, total_emails, status) VALUES (?, ?, ?, 'empty.csv', 0, 'pending')", [self.empty_job_id, self.user_id, self.ws_id])

    def tearDown(self):
        try:
            self.db.execute("DELETE FROM verification_jobs WHERE id = ?", [self.empty_job_id])
            self.db.execute("DELETE FROM users WHERE id = ?", [self.user_id])
            self.db.execute("DELETE FROM workspaces WHERE id = ?", [self.ws_id])
        except Exception:
            pass

    def test_no_fake_timeline_events(self):
        # When no job_events exist, timeline returns an empty list (no fake generated steps)
        events = history_service.get_job_timeline(self.empty_job_id, self.user_id, self.ws_id, "user")
        self.assertEqual(events, [])

    def test_no_fake_diagnostics_string(self):
        diag = history_service.get_job_diagnostics(self.empty_job_id, self.user_id, self.ws_id, "user")
        self.assertNotIn("provider_responses", diag)
        self.assertEqual(diag["smtp_errors_count"], 0)
        self.assertEqual(diag["dns_errors_count"], 0)
        self.assertEqual(diag["timeouts_count"], 0)

    def test_no_fake_dashboard_counts(self):
        summary = dashboard_service.get_verification_summary(self.user_id, self.ws_id)
        # Empty workspace should return 0 for all counts, not 1420 deliverable
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["counts"]["deliverable"], 0)
        self.assertEqual(summary["counts"]["invalid"], 0)

    def test_no_fake_analytics_overview(self):
        overview = analytics_service.get_analytics_overview(self.user_id, self.ws_id, "user")
        # Empty workspace should return 0 verified, not 12500
        self.assertEqual(overview["total_emails_verified"], 0)
        self.assertEqual(overview["deliverable_percentage"], 0.0)


class TestHardcodedSecretsRemoved(unittest.TestCase):
    """Test that default backdoor accounts are removed."""

    def test_no_default_admin_backdoor(self):
        db = get_db()
        backdoor = db.execute("SELECT id FROM users WHERE email = 'admin@example.com'").fetchone()
        self.assertIsNone(backdoor, "Default backdoor admin@example.com must not exist in DB")


class TestCreditAllocationAndBalanceSync(unittest.TestCase):
    """Test that admin credit allocations are accurately stored and reflected in user responses."""

    def setUp(self):
        self.db = get_db()
        self.user_id = str(uuid.uuid4())
        self.email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        self.db.execute("""
            INSERT INTO users (id, email, role, is_active, credit_pool, credits)
            VALUES (?, ?, 'user', TRUE, 0, 0)
        """, [self.user_id, self.email])

    def tearDown(self):
        try:
            self.db.execute("DELETE FROM users WHERE id = ?", [self.user_id])
        except Exception:
            pass

    def test_credit_allocation_reflected_in_user_response(self):
        from auth import _row_to_user, _select_user_by_id

        # Admin allocates 1,000 credits
        self.db.execute(
            "UPDATE users SET credit_pool = GREATEST(0, credit_pool + ?), credits = GREATEST(0, COALESCE(credits, 0) + ?) WHERE id = ?",
            [1000, 1000, self.user_id]
        )

        user_row = _select_user_by_id(self.db, self.user_id)
        user_res = _row_to_user(user_row)

        self.assertEqual(user_res.credit_pool, 1000)
        self.assertEqual(user_res.credits, 1000)

        # Consume 1 credit
        self.db.execute(
            "UPDATE users SET credit_pool = GREATEST(0, credit_pool - 1), credits = GREATEST(0, COALESCE(credits, 0) - 1) WHERE id = ?",
            [self.user_id]
        )

        updated_row = _select_user_by_id(self.db, self.user_id)
        updated_res = _row_to_user(updated_row)
        self.assertEqual(updated_res.credit_pool, 999)
        self.assertEqual(updated_res.credits, 999)


class TestUsageSummaryCalculation(unittest.TestCase):
    """Test that account usage summary accurately computes metrics from verification_jobs."""

    def setUp(self):
        self.db = get_db()
        self.user_id = str(uuid.uuid4())
        self.ws_id = str(uuid.uuid4())
        self.email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        self.db.execute("""
            INSERT INTO users (id, email, role, is_active, workspace_id, credit_pool, credits)
            VALUES (?, ?, 'user', TRUE, ?, 950, 950)
        """, [self.user_id, self.email, self.ws_id])

        # Create 3 verification jobs (total 50 processed emails: 40 deliverable, 10 invalid)
        self.job1 = str(uuid.uuid4())
        self.job2 = str(uuid.uuid4())
        self.job3 = str(uuid.uuid4())

        self.db.execute("""
            INSERT INTO verification_jobs (id, user_id, workspace_id, file_name, total_emails, processed_emails, deliverable_count, invalid_count, status, created_at)
            VALUES (?, ?, ?, 'list1.csv', 20, 20, 16, 4, 'completed', CURRENT_TIMESTAMP)
        """, [self.job1, self.user_id, self.ws_id])

        self.db.execute("""
            INSERT INTO verification_jobs (id, user_id, workspace_id, file_name, total_emails, processed_emails, deliverable_count, invalid_count, status, created_at)
            VALUES (?, ?, ?, 'list2.csv', 20, 20, 16, 4, 'completed', CURRENT_TIMESTAMP)
        """, [self.job2, self.user_id, self.ws_id])

        self.db.execute("""
            INSERT INTO verification_jobs (id, user_id, workspace_id, file_name, total_emails, processed_emails, deliverable_count, invalid_count, status, created_at)
            VALUES (?, ?, ?, 'list3.csv', 10, 10, 8, 2, 'completed', CURRENT_TIMESTAMP)
        """, [self.job3, self.user_id, self.ws_id])

    def tearDown(self):
        try:
            self.db.execute("DELETE FROM verification_jobs WHERE user_id = ?", [self.user_id])
            self.db.execute("DELETE FROM users WHERE id = ?", [self.user_id])
        except Exception:
            pass

    def test_usage_summary_matches_job_data(self):
        from services import account_service

        usage = account_service.get_usage_summary(self.user_id, self.ws_id, "user")

        self.assertEqual(usage["recent_jobs"], 3)
        self.assertEqual(usage["total_verified"], 50)
        self.assertEqual(usage["verifications_today"], 50)
        self.assertEqual(usage["verifications_month"], 50)
        self.assertEqual(usage["success_rate"], 80.0)
        self.assertIsNotNone(usage["last_verification"])


if __name__ == "__main__":
    unittest.main()
