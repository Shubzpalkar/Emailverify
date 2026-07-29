import os
import json
import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger("verification_engine.provider")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "provider_rules.json")

class ProviderEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProviderEngine, cls).__new__(cls)
            cls._instance._load_config()
            cls._instance._provider_cache = {}
        return cls._instance

    def _load_config(self):
        self.providers = []
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.providers = data.get("providers", [])
                logger.info(f"Loaded {len(self.providers)} provider behavior profiles from config/provider_rules.json")
            else:
                logger.warning(f"Provider rules file not found at {CONFIG_PATH}, using default rules")
        except Exception as e:
            logger.error(f"Error loading provider rules: {e}")

    def detect_provider(self, mx_records: List[str], banner: str = "", domain: str = "") -> Dict[str, Any]:
        """
        Fingerprint provider based on MX host patterns, SMTP banner, and domain name.
        Returns dict with provider_name, provider_type, and rules.
        """
        cache_key = f"{','.join(mx_records)}|{banner[:30]}"
        if cache_key in self._provider_cache:
            return self._provider_cache[cache_key]

        mx_str = ",".join(mx_records).lower() if mx_records else ""
        banner_lower = banner.lower()
        domain_lower = domain.lower()

        # Match against loaded provider profiles
        for p in self.providers:
            name = p.get("name")
            ptype = p.get("type", "unknown")
            mx_patterns = p.get("mx_patterns", [])
            banner_patterns = p.get("banner_patterns", [])
            rules = p.get("rules", {})

            # Check MX hostname match
            for pat in mx_patterns:
                if pat and pat.lower() in mx_str:
                    res = {"provider_name": name, "provider_type": ptype, "rules": rules}
                    self._provider_cache[cache_key] = res
                    return res

            # Check Banner match
            for pat in banner_patterns:
                if pat and pat.lower() in banner_lower:
                    res = {"provider_name": name, "provider_type": ptype, "rules": rules}
                    self._provider_cache[cache_key] = res
                    return res

        # Self-Hosted / On-Premise check
        if domain_lower and domain_lower in mx_str:
            res = {
                "provider_name": "Self-Hosted / Exchange On-Prem",
                "provider_type": "on_premise",
                "rules": {"max_concurrent": 5}
            }
            self._provider_cache[cache_key] = res
            return res

        # Fallback
        res = {
            "provider_name": "Generic / Custom",
            "provider_type": "unknown",
            "rules": {"max_concurrent": 5}
        }
        self._provider_cache[cache_key] = res
        return res

provider_engine = ProviderEngine()
