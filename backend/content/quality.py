"""Quality checker for generated content."""

import re
from dataclasses import dataclass, field


@dataclass
class QualityResult:
    passed: bool
    notes: list[str]
    checks: dict[str, bool]


class QualityChecker:
    """Runs a suite of quality checks on generated content."""

    # Wrong URLs that should never appear in content
    WRONG_URLS = [
        "api.soxai.com",
        "www.soxai.com/api",
    ]

    # Misspellings to detect (word-boundary patterns that won't match URLs)
    # We allow lowercase 'soxai' only when it appears as part of a domain (e.g. soxai.io)
    BRAND_MISSPELLINGS = [
        r"\bSoxai\b(?!\s*\.)",   # wrong capitalisation: SoxAI not Soxai (not followed by dot)
        r"\bSOXAI\b",            # all caps wrong
        r"\bOpenrouter\b",       # wrong capitalisation: OpenRouter not Openrouter
        r"\bopenrouter\b(?!\s*\.)",  # all lowercase (not a domain)
        r"\bOPENROUTER\b",       # all caps wrong
    ]

    # Placeholder patterns
    PLACEHOLDER_PATTERNS = [
        r"\[TODO\]",
        r"\[INSERT",
        r"Lorem ipsum",
        r"\bTBD\b",
    ]

    # Platform character limits
    PLATFORM_LIMITS = {
        "twitter": 280,
    }

    # Platform minimum lengths
    PLATFORM_MINIMUMS = {
        "zhihu": 500,
        "blog": 1000,
    }

    def check(
        self,
        title: str,
        body: str,
        platform: str,
        language: str,
    ) -> QualityResult:
        checks: dict[str, bool] = {}
        notes: list[str] = []

        # 1. No false claims (wrong URLs)
        wrong_urls_found = [url for url in self.WRONG_URLS if url in body or url in title]
        checks["no_false_claims"] = len(wrong_urls_found) == 0
        if wrong_urls_found:
            notes.append(f"Wrong URL(s) found: {', '.join(wrong_urls_found)}")

        # 2. Brand consistent (correct capitalisation)
        brand_errors = [
            pattern for pattern in self.BRAND_MISSPELLINGS
            if re.search(pattern, body) or re.search(pattern, title)
        ]
        checks["brand_consistent"] = len(brand_errors) == 0
        if brand_errors:
            notes.append(f"Brand name misspelling detected (patterns: {brand_errors})")

        # 3. Platform adapted (length constraints)
        body_length = len(body)
        platform_lower = platform.lower()

        platform_ok = True
        if platform_lower in self.PLATFORM_LIMITS:
            limit = self.PLATFORM_LIMITS[platform_lower]
            if body_length > limit:
                platform_ok = False
                notes.append(
                    f"Content too long for {platform}: {body_length} chars (max {limit})"
                )
        if platform_lower in self.PLATFORM_MINIMUMS:
            minimum = self.PLATFORM_MINIMUMS[platform_lower]
            if body_length < minimum:
                platform_ok = False
                notes.append(
                    f"Content too short for {platform}: {body_length} chars (min {minimum})"
                )
        checks["platform_adapted"] = platform_ok

        # 4. No placeholders
        placeholders_found = [
            p for p in self.PLACEHOLDER_PATTERNS
            if re.search(p, body, re.IGNORECASE)
        ]
        checks["no_placeholders"] = len(placeholders_found) == 0
        if placeholders_found:
            notes.append(f"Placeholder text found: {placeholders_found}")

        # 5. Proper format (blog must have ## headings)
        proper_format = True
        if platform_lower == "blog":
            if not re.search(r"^##\s+.+", body, re.MULTILINE):
                proper_format = False
                notes.append("Blog content must contain at least one ## heading")
        checks["proper_format"] = proper_format

        passed = all(checks.values())
        return QualityResult(passed=passed, notes=notes, checks=checks)
