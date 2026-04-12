import re
from dataclasses import dataclass


@dataclass
class LeadSignal:
    detected: bool
    signal_type: str  # team_size | budget | compliance | migration | procurement | none
    confidence: float


# Each entry: (signal_type, base_confidence, english_patterns, chinese_patterns)
# English patterns use \b word boundaries; Chinese patterns do not (CJK has no word boundaries).
_PATTERNS: list[tuple[str, float, list[str], list[str]]] = [
    (
        "team_size",
        0.8,
        [
            r"\b(\d+)\s*(developers?|engineers?|users?|members?|employees?)\b",
            r"\bteam\s+of\s+\d+\b",
            r"\b(large|enterprise|big)\s+team\b",
        ],
        [
            r"(我们|我司|公司).{0,10}(\d+)\s*(人|名)",
            r"\d+\s*名.{0,5}(开发|工程师|用户)",
            r"(\d+)\s*(人|开发者|工程师)",
        ],
    ),
    (
        "budget",
        0.9,
        [
            r"\b(budget|pricing|cost|price|spend|invoice|quote|quotation)\b",
            r"\$\s*\d+[kKmM]?\b",
            r"\b\d+\s*(dollars?|USD|per\s+month|monthly|annually)\b",
            r"\b(how\s+much|what.{0,10}cost|pricing\s+plan)\b",
        ],
        [
            r"(预算|报价|价格|费用|成本|月费|年费|采购金额)",
        ],
    ),
    (
        "compliance",
        0.85,
        [
            r"\b(SOC\s*2|ISO\s*27001|HIPAA|GDPR|PCI.?DSS|FedRAMP)\b",
            r"\b(compliance|audit|certification|regulatory|data\s+residency)\b",
            r"\b(security\s+review|penetration\s+test|pen\s+test|vulnerability)\b",
        ],
        [
            r"(合规|审计|认证|数据合规|等保|GDPR|隐私)",
        ],
    ),
    (
        "migration",
        0.75,
        [
            r"\b(migrat|switching\s+from|moving\s+(from|away\s+from)|replac)\w*\b",
            r"\bcurrently\s+using\b",
            r"\b(OpenAI\s+direct|Azure\s+OpenAI|Bedrock|Vertex).{0,30}(switch|migrat|replac)\b",
        ],
        [
            r"(迁移|切换|替换|换掉).{0,20}(方案|平台|服务|供应商)",
            r"(我们|目前|现在)用.{0,20}(迁移|切换)",
        ],
    ),
    (
        "procurement",
        0.85,
        [
            r"\b(procurement|purchase\s+order|PO|contract|vendor|RFP|RFQ|evaluation)\b",
            r"\b(legal\s+(review|team)|security\s+team|IT\s+department|CTO|CIO)\b",
            r"\b(pilot|proof\s+of\s+concept|POC|trial\s+period|evaluation\s+period)\b",
        ],
        [
            r"(采购|招标|合同|供应商|评估|甲方|乙方|框架协议)",
        ],
    ),
]


class LeadDetector:
    def detect(self, message: str) -> LeadSignal:
        """Detect lead signals in a message using regex patterns."""
        for signal_type, base_confidence, en_patterns, zh_patterns in _PATTERNS:
            for pattern in en_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return LeadSignal(
                        detected=True,
                        signal_type=signal_type,
                        confidence=base_confidence,
                    )
            for pattern in zh_patterns:
                if re.search(pattern, message):
                    return LeadSignal(
                        detected=True,
                        signal_type=signal_type,
                        confidence=base_confidence,
                    )

        return LeadSignal(detected=False, signal_type="none", confidence=0.0)
