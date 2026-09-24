import unittest
import asyncio
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
settings.DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_verification.db")

from dns_checks import classify_dns_exception, detect_provider_details, dns_health_monitor
from smtp_verifier import map_smtp_response, get_domain_semaphore
from provider_engine import provider_engine
from engine import check_syntax, check_role, compute_quality_and_confidence, map_to_legacy_status, engine_metrics

class TestDNSHealthAndDualResolution(unittest.TestCase):

    def test_dns_health_monitor_recording(self):
        healthy_resolvers = dns_health_monitor.get_healthy_resolvers()
        self.assertTrue(len(healthy_resolvers) > 0)
        best_ip = dns_health_monitor.get_best_resolver_ip()
        self.assertIn(".", best_ip)

        dns_health_monitor.record_result(best_ip, success=True, latency_ms=12.5)
        metrics = dns_health_monitor.get_metrics_summary()
        self.assertTrue(isinstance(metrics, list))
        self.assertTrue(len(metrics) > 0)

    def test_timeout_classification(self):
        status, reason, retryable = classify_dns_exception(asyncio.TimeoutError())
        self.assertEqual(status, "timeout")
        self.assertTrue(retryable)

    def test_nxdomain_classification(self):
        class MockDNSError(Exception):
            args = (4, "domain name not found")
        
        status, reason, retryable = classify_dns_exception(MockDNSError())
        self.assertEqual(status, "nxdomain")
        self.assertFalse(retryable)

    def test_servfail_classification(self):
        class MockDNSError(Exception):
            args = (2, "SERVFAIL")
            
        status, reason, retryable = classify_dns_exception(MockDNSError())
        self.assertEqual(status, "servfail")
        self.assertTrue(retryable)


class TestProviderIntelligenceEngine(unittest.TestCase):

    def test_microsoft365_fingerprint(self):
        res = provider_engine.detect_provider(["domain-com.mail.protection.outlook.com"], "", "domain.com")
        self.assertEqual(res["provider_name"], "Microsoft 365")
        self.assertEqual(res["provider_type"], "cloud_workspace")
        self.assertTrue(res["rules"].get("hide_mailbox_existence", False))

    def test_google_workspace_fingerprint(self):
        res = provider_engine.detect_provider(["aspmx.l.google.com"], "", "domain.com")
        self.assertEqual(res["provider_name"], "Google Workspace")
        self.assertEqual(res["provider_type"], "cloud_workspace")

    def test_proofpoint_fingerprint(self):
        res = provider_engine.detect_provider(["mxa-001b.pphosted.com"], "", "domain.com")
        self.assertEqual(res["provider_name"], "Proofpoint")
        self.assertEqual(res["provider_type"], "gateway")

    def test_mimecast_fingerprint(self):
        res = provider_engine.detect_provider(["us-smtp-inbound-1.mimecast.com"], "", "domain.com")
        self.assertEqual(res["provider_name"], "Mimecast")

    def test_barracuda_fingerprint(self):
        res = provider_engine.detect_provider(["barracuda.domain.com"], "", "domain.com")
        self.assertEqual(res["provider_name"], "Barracuda")

    def test_cisco_fingerprint(self):
        res = provider_engine.detect_provider(["iphmx.com"], "", "domain.com")
        self.assertEqual(res["provider_name"], "Cisco Secure Email")

    def test_postfix_banner_fingerprint(self):
        res = provider_engine.detect_provider([], "220 mail.domain.com ESMTP Postfix", "domain.com")
        self.assertEqual(res["provider_name"], "Postfix")


class TestSMTPResponseMappingAndConcurrency(unittest.TestCase):

    def test_domain_semaphore(self):
        sem1 = get_domain_semaphore("example.com", max_concurrent=5)
        sem2 = get_domain_semaphore("EXAMPLE.COM", max_concurrent=5)
        self.assertEqual(sem1, sem2)

    def test_code_250(self):
        status, reason = map_smtp_response(250, "2.1.5 OK")
        self.assertEqual(status, "Deliverable")

    def test_code_451_greylisted(self):
        status, reason = map_smtp_response(451, "Greylisted, please try again later")
        self.assertEqual(status, "Greylisted")

    def test_code_452_mailbox_full(self):
        status, reason = map_smtp_response(452, "Insufficient system storage")
        self.assertEqual(status, "Mailbox Full")

    def test_code_422_mailbox_full(self):
        status, reason = map_smtp_response(422, "Mailbox over quota")
        self.assertEqual(status, "Mailbox Full")

    def test_code_500_503_protected(self):
        status1, _ = map_smtp_response(500, "Syntax error, command unrecognized")
        status2, _ = map_smtp_response(503, "Bad sequence of commands")
        self.assertEqual(status1, "Protected")
        self.assertEqual(status2, "Protected")

    def test_code_530_535_protected(self):
        status1, _ = map_smtp_response(530, "Authentication required")
        status2, _ = map_smtp_response(535, "Authentication credentials invalid")
        self.assertEqual(status1, "Protected")
        self.assertEqual(status2, "Protected")

    def test_code_571_protected(self):
        status, _ = map_smtp_response(571, "Delivery not authorized")
        self.assertEqual(status, "Protected")

    def test_code_550_user_unknown(self):
        status, reason = map_smtp_response(550, "5.1.1 User unknown")
        self.assertEqual(status, "Undeliverable")

    def test_code_554_antispam(self):
        status, reason = map_smtp_response(554, "Transaction failed: blocked by spam filter")
        self.assertEqual(status, "Protected")

    def test_code_0_connection_refused(self):
        status, reason = map_smtp_response(0, "Connection refused by peer")
        self.assertEqual(status, "Protected")


class TestQualityScoringMetricsAndLegacyStatus(unittest.TestCase):

    def test_deliverable_good(self):
        quality, conf = compute_quality_and_confidence("Deliverable")
        self.assertEqual(quality, "Good")
        self.assertGreaterEqual(conf, 0.90)

    def test_catch_all_risky(self):
        quality, conf = compute_quality_and_confidence("Catch-All")
        self.assertEqual(quality, "Risky")

    def test_undeliverable_bad(self):
        quality, conf = compute_quality_and_confidence("Undeliverable")
        self.assertEqual(quality, "Bad")
        self.assertEqual(conf, 0.0)

    def test_invalid_domain_bad(self):
        quality, conf = compute_quality_and_confidence("Invalid Domain")
        self.assertEqual(quality, "Bad")
        self.assertEqual(conf, 0.0)

    def test_protected_risky(self):
        quality, conf = compute_quality_and_confidence("Protected")
        self.assertEqual(quality, "Risky")

    def test_legacy_status_mapping(self):
        self.assertEqual(map_to_legacy_status("Deliverable", False, False), "valid")
        self.assertEqual(map_to_legacy_status("Deliverable", True, False), "role_based")
        self.assertEqual(map_to_legacy_status("Greylisted", False, False), "greylisted")
        self.assertEqual(map_to_legacy_status("Protected", False, False), "protected")
        self.assertEqual(map_to_legacy_status("Mailbox Full", False, False), "mailbox_full")
        self.assertEqual(map_to_legacy_status("Undeliverable", False, False), "invalid")

    def test_engine_metrics_recording(self):
        engine_metrics.record_verification("Deliverable", "Google Workspace", latency_ms=150.0, dns_ms=10.0, smtp_ms=140.0)
        summary = engine_metrics.get_summary()
        self.assertGreaterEqual(summary["total_verifications"], 1)
        self.assertIn("Google Workspace", summary["provider_distribution"])


class TestSyntaxAndRole(unittest.TestCase):

    def test_valid_syntax(self):
        self.assertTrue(check_syntax("user@example.com"))

    def test_long_tlds_syntax(self):
        # Support valid long modern TLDs
        self.assertTrue(check_syntax("user@company.international"))
        self.assertTrue(check_syntax("hello@agency.photography"))
        self.assertTrue(check_syntax("contact@tech.engineering"))
        self.assertTrue(check_syntax("info@business.consulting"))
        self.assertTrue(check_syntax("dev@platform.solutions"))
        self.assertTrue(check_syntax("founder@startup.technology"))

    def test_double_dot_invalid(self):
        self.assertFalse(check_syntax("user..name@example.com"))
        self.assertFalse(check_syntax("user@example..com"))

    def test_invalid_syntax_formats(self):
        self.assertFalse(check_syntax("missing-at-sign.com"))
        self.assertFalse(check_syntax("@missing-local.com"))
        self.assertFalse(check_syntax("user@"))
        self.assertFalse(check_syntax("user@.com"))
        self.assertFalse(check_syntax("user@-domain.com"))
        self.assertFalse(check_syntax("user@domain-.com"))

    def test_role_account(self):
        self.assertTrue(check_role("support@example.com"))
        self.assertTrue(check_role("admin@example.com"))
        self.assertTrue(check_role("billing@example.com"))
        self.assertTrue(check_role("security@example.com"))
        self.assertFalse(check_role("john.doe@example.com"))


class TestDisposableAndCatchAllLogic(unittest.TestCase):

    def test_disposable_domain_detection(self):
        from engine import check_disposable
        self.assertTrue(check_disposable("mailinator.com"))
        self.assertTrue(check_disposable("tempmail.com"))
        self.assertTrue(check_disposable("10minutemail.com"))
        self.assertTrue(check_disposable("guerrillamail.com"))
        self.assertTrue(check_disposable("sub.mailinator.com"))
        self.assertFalse(check_disposable("gmail.com"))
        self.assertFalse(check_disposable("microsoft.com"))

    def test_smtp_greeting_never_deliverable(self):
        # 220 banner or 221 quit must NEVER be mapped to Deliverable
        status_220, _ = map_smtp_response(220, "220 mx.example.com ESMTP ready")
        status_221, _ = map_smtp_response(221, "221 Bye")
        self.assertNotEqual(status_220, "Deliverable")
        self.assertNotEqual(status_221, "Deliverable")
        self.assertEqual(status_220, "Temporary Failure")
        self.assertEqual(status_221, "Temporary Failure")

    def test_explicit_rejection_vs_protection(self):
        # 550 User Unknown -> Undeliverable (Bad / Invalid)
        status_unknown, _ = map_smtp_response(550, "5.1.1 <nobody@example.com>: Recipient address rejected: User unknown in virtual mailbox table")
        self.assertEqual(status_unknown, "Undeliverable")

        # 550 Blacklisted/Spam -> Protected (Risky, NOT Invalid)
        status_spam, _ = map_smtp_response(550, "5.7.1 Service unavailable; Client host blocked using Spamhaus")
        self.assertEqual(status_spam, "Protected")

        # 554 Relay Access Denied / Security Filter -> Protected
        status_relay, _ = map_smtp_response(554, "5.7.1 Relay access denied")
        self.assertEqual(status_relay, "Protected")

    def test_temporary_4xx_responses(self):
        status_421, _ = map_smtp_response(421, "4.2.1 Service not available, closing transmission channel")
        status_450, _ = map_smtp_response(450, "4.2.0 Mailbox busy")
        status_451, _ = map_smtp_response(451, "4.7.1 Greylisting in action, please come back in 300 seconds")
        self.assertEqual(status_421, "Temporary Failure")
        self.assertEqual(status_450, "Temporary Failure")
        self.assertEqual(status_451, "Greylisted")


class TestMXFailoverSimulation(unittest.IsolatedAsyncioTestCase):

    async def test_mx_failover_loop(self):
        import unittest.mock as mock
        from engine import verify_single_email

        # Mock resolve_domain_detail to return 2 MX records: primary_mx (fails) and backup_mx (succeeds)
        mock_dns = {
            "dns_status": "valid",
            "resolver": "1.1.1.1",
            "reason": "MX records resolved",
            "latency_ms": 10.0,
            "retryable": False,
            "confidence": 1.0,
            "mx_records": ["primary-failing.example.com", "backup-working.example.com"],
            "has_a_record": True
        }

        async def mock_smtp(mx_host, email, sender_email=None, helo_host=None):
            if mx_host == "primary-failing.example.com":
                return {
                    "status": "Temporary Failure",
                    "smtp_code": 0,
                    "reason": "SMTP connection timed out",
                    "raw_message": "Timeout",
                    "tls_used": False,
                    "smtp_transcript": {}
                }
            elif mx_host == "backup-working.example.com":
                return {
                    "status": "Deliverable",
                    "smtp_code": 250,
                    "reason": "Recipient address accepted",
                    "raw_message": "250 OK",
                    "tls_used": True,
                    "smtp_transcript": {"starttls": True}
                }

        with mock.patch("engine.resolve_domain_detail", return_value=mock_dns), \
             mock.patch("engine.verify_smtp_with_retries", side_effect=mock_smtp), \
             mock.patch("engine.check_catch_all_detailed", return_value={"is_catch_all": False}), \
             mock.patch("engine.get_email_cache", return_value=None), \
             mock.patch("engine.get_domain_intelligence", return_value=None):
            
            res = await verify_single_email("testuser@example.com", check_catch_all=True)
            self.assertEqual(res["status"], "valid")
            self.assertEqual(res["detailed_status"], "Deliverable")
            self.assertEqual(res["mx_server"], "backup-working.example.com")

    async def test_dns_timeout_returns_unknown_not_invalid(self):
        import unittest.mock as mock
        from engine import verify_single_email

        mock_dns = {
            "dns_status": "timeout",
            "resolver": "1.1.1.1",
            "reason": "DNS lookup timed out",
            "latency_ms": 5000.0,
            "retryable": True,
            "confidence": 0.30,
            "mx_records": [],
            "has_a_record": False
        }

        with mock.patch("engine.resolve_domain_detail", return_value=mock_dns), \
             mock.patch("engine.get_email_cache", return_value=None):
            res = await verify_single_email("user@dns-timeout-domain.com")
            # Must NEVER return invalid for DNS timeout
            self.assertEqual(res["status"], "unknown")
            self.assertEqual(res["detailed_status"], "DNS Timeout")
            self.assertEqual(res["quality"], "Risky")
            self.assertTrue(res["retryable"])

    async def test_catch_all_domain_returns_catch_all_not_valid(self):
        import unittest.mock as mock
        from engine import verify_single_email

        mock_dns = {
            "dns_status": "valid",
            "resolver": "1.1.1.1",
            "reason": "MX resolved",
            "latency_ms": 10.0,
            "retryable": False,
            "confidence": 1.0,
            "mx_records": ["mx.catchall.com"],
            "has_a_record": True
        }

        # Even if target email returns 250, catch-all domain must be labeled Catch-All, NOT valid/deliverable
        mock_smtp_res = {
            "status": "Deliverable",
            "smtp_code": 250,
            "reason": "250 OK",
            "raw_message": "250 OK",
            "tls_used": True,
            "smtp_transcript": {}
        }

        with mock.patch("engine.resolve_domain_detail", return_value=mock_dns), \
             mock.patch("engine.verify_smtp_with_retries", return_value=mock_smtp_res), \
             mock.patch("engine.check_catch_all_detailed", return_value={"is_catch_all": True}), \
             mock.patch("engine.get_email_cache", return_value=None), \
             mock.patch("engine.get_domain_intelligence", return_value=None):
            res = await verify_single_email("anyuser@catchall.com", check_catch_all=True)
            self.assertEqual(res["status"], "catch_all")
            self.assertEqual(res["detailed_status"], "Catch-All")
            self.assertEqual(res["quality"], "Risky")

    async def test_provider_protection_returns_protected_not_invalid(self):
        import unittest.mock as mock
        from engine import verify_single_email

        mock_dns = {
            "dns_status": "valid",
            "resolver": "1.1.1.1",
            "reason": "MX resolved",
            "latency_ms": 10.0,
            "retryable": False,
            "confidence": 1.0,
            "mx_records": ["mx.protected-corp.com"],
            "has_a_record": True
        }

        mock_smtp_res = {
            "status": "Protected",
            "smtp_code": 550,
            "reason": "Blocked by Spamhaus / policy rejection",
            "raw_message": "550 5.7.1 Blocked",
            "tls_used": False,
            "smtp_transcript": {}
        }

        with mock.patch("engine.resolve_domain_detail", return_value=mock_dns), \
             mock.patch("engine.verify_smtp_with_retries", return_value=mock_smtp_res), \
             mock.patch("engine.check_catch_all_detailed", return_value={"is_catch_all": False}), \
             mock.patch("engine.get_email_cache", return_value=None), \
             mock.patch("engine.get_domain_intelligence", return_value=None):
            res = await verify_single_email("user@protected-corp.com")
            # Anti-spam block must NOT be marked as invalid
            self.assertEqual(res["status"], "protected")
            self.assertEqual(res["detailed_status"], "Protected")
            self.assertEqual(res["quality"], "Risky")

    async def test_explicit_user_unknown_returns_invalid(self):
        import unittest.mock as mock
        from engine import verify_single_email

        mock_dns = {
            "dns_status": "valid",
            "resolver": "1.1.1.1",
            "reason": "MX resolved",
            "latency_ms": 10.0,
            "retryable": False,
            "confidence": 1.0,
            "mx_records": ["mail.targetcorp.com"],
            "has_a_record": True
        }

        mock_smtp_res = {
            "status": "Undeliverable",
            "smtp_code": 550,
            "reason": "550 5.1.1 User unknown",
            "raw_message": "550 5.1.1 User unknown",
            "tls_used": False,
            "smtp_transcript": {}
        }

        with mock.patch("engine.resolve_domain_detail", return_value=mock_dns), \
             mock.patch("engine.verify_smtp_with_retries", return_value=mock_smtp_res), \
             mock.patch("engine.check_catch_all_detailed", return_value={"is_catch_all": False}), \
             mock.patch("engine.get_email_cache", return_value=None), \
             mock.patch("engine.get_domain_intelligence", return_value=None):
            res = await verify_single_email("nonexistent@targetcorp.com")
            self.assertEqual(res["status"], "invalid")
            self.assertEqual(res["detailed_status"], "Undeliverable")
            self.assertEqual(res["quality"], "Bad")
            self.assertEqual(res["confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
