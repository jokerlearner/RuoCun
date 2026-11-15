"""识别并脱敏可能的凭据，用于持久记忆写入前的安全处理。"""

import re

_SELF_KEY = "".join(("sk", "-"))
_PATTERNS = (
    ("私钥块", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b", re.ASCII)),
    ("AWS Secret", re.compile(r"""aws_secret_access_key\s*[=:]\s*['"]?[A-Za-z0-9/+]{40}""", re.I)),
    ("GitHub Token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b", re.ASCII)),
    ("Slack Token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}", re.ASCII)),
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b", re.ASCII)),
    ("Stripe 密钥", re.compile(r"\bsk_live_[0-9A-Za-z]{24,}\b", re.ASCII)),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}\b", re.ASCII)),
    ("sk- 风格密钥", re.compile(rf"\b{_SELF_KEY}[A-Za-z0-9]{{20,}}\b", re.ASCII)),
    ("密钥赋值", re.compile(r"""(?a:\b(api[_-]?key|secret|token|password|passwd)\b)\s*[=:]\s*['"][^'"\s]{12,}['"]""", re.I)),
)


def findSecrets(text: str) -> list[str]:
    return [name for name, pattern in _PATTERNS if pattern.search(text)]


def redactSecrets(text: str) -> str:
    for name, pattern in _PATTERNS:
        text = pattern.sub(f"[已隐去:{name}]", text)
    return text
