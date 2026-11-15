"""识别覆盖任意命令或整类解释器的宽泛 Bash 允许规则，供自动模式判断。"""

_PATTERNS = (
    "python", "python3", "python2", "node", "deno", "tsx", "ruby", "perl", "php", "lua",
    "npx", "bunx", "npm run", "yarn run", "pnpm run", "bun run", "bash", "sh", "zsh", "fish",
    "ssh", "eval", "exec", "env", "xargs", "sudo",
)


def isDangerousBashPermission(ruleSpec: str | None) -> bool:
    if ruleSpec is None or ruleSpec == "":
        return True
    content = ruleSpec.strip().lower()
    return content == "*" or any(
        content in (pattern, pattern + ":*", pattern + "*", pattern + " *")
        or (content.startswith(pattern + " -") and content.endswith("*"))
        for pattern in _PATTERNS
    )
