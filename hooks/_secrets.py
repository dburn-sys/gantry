"""Secret detection for Gantry hooks. Standard library only."""
import math
import re
from dataclasses import dataclass

KNOWN = [
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("slack-token", re.compile(r"\bxox[bp]-[A-Za-z0-9-]{10,}\b")),
    ("payment-live-key", re.compile(r"\bsk_live_[A-Za-z0-9]{24,}\b")),
    ("cloud-access-key", re.compile(r"\bAKIA[A-Z0-9]{16}\b")),
]
ASSIGNMENT = re.compile(
    r"(?i)(secret|token|passw(or)?d|api[_-]?key|signing[_-]?key)\w*"
    r"\s*[:=]\s*[\"']([^\"'\n]{12,})[\"']"
)
PLACEHOLDER = re.compile(r"(?i)changeme|example|placeholder|your-|xxx|dummy")
REFERENCE = re.compile(r"process\.env|os\.environ|\$\{|\$[A-Z_]+")


@dataclass
class Finding:
    kind: str
    line: int
    preview: str


def entropy(value: str) -> float:
    counts = {c: value.count(c) for c in set(value)}
    return -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values())


def redact(value: str) -> str:
    return value[:4] + "***"


def scan(text: str) -> list[Finding]:
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in KNOWN:
            for m in pattern.finditer(line):
                findings.append(Finding(kind, number, redact(m.group(0))))
        for m in ASSIGNMENT.finditer(line):
            value = m.group(3)
            if PLACEHOLDER.search(value) or REFERENCE.search(value):
                continue
            if entropy(value) > 3.5:
                findings.append(Finding("assignment", number, redact(value)))
    return findings
