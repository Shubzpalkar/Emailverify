import unittest
import asyncio
import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

    def test_double_dot_invalid(self):
        self.assertFalse(check_syntax("user..name@example.com"))

    def test_role_account(self):
        self.assertTrue(check_role("support@example.com"))
        self.assertFalse(check_role("john.doe@example.com"))


if __name__ == "__main__":
    unittest.main()
