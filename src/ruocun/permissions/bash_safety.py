"""通过已知模式识别危险命令和只读命令，供权限引擎处理需要额外确认的操作。"""
from __future__ import annotations

import re

from .rules import splitBashCommands

_DEV_NULL = re.compile(r"\s*&?\d*>>?\s*(/dev/null\b|&\d+\b)", re.ASCII)
_READONLY = set("ls pwd cat head tail wc file stat du df tree echo printf which type whereis basename dirname realpath readlink date whoami hostname uname id env printenv uptime locale grep egrep fgrep rg ag sort uniq cut nl column comm tr tac rev fold expand cksum sha1sum sha256sum md5 md5sum diff cmp jq yq xxd od strings cd".split())
_GIT = set("status log diff show branch remote tag describe rev-parse ls-files ls-tree blame shortlog reflog whatchanged cat-file for-each-ref name-rev symbolic-ref rev-list Config".split())


def _has(pattern: str, value: str, *, sensitive: bool = False) -> bool:
    return re.search(pattern, value, re.ASCII | (0 if sensitive else re.IGNORECASE)) is not None


def _cmd(name: str, value: str) -> bool:
    return _has(r"(^|\s)" + name + r"(?=\s|$|;|&|\|)", value)


def _dangerSegment(segment: str) -> str | None:
    s = re.sub(r"(^|\s)cd\s+([^\s;&|]+)", r"\1cd __DIR__", segment, flags=re.IGNORECASE | re.ASCII)
    if _cmd("rm", s) and _has(r"(^|\s)-\S*r", s):
        if _has(r"\s(/|~|\$home)(\s|/|$)", s) or _has(r"\s/\*(\s|$)|(^|\s)\*(\s|$)|\s~/", s):
            return "rm 递归删除根/家目录/通配,可能毁坏系统"
    if _has(r"\b(dd|tee)\b[^|]*of=\s*/dev/(sd|nvme|disk|hd)|>\s*/dev/(sd|nvme|disk|hd)", s):
        return "写入裸磁盘设备"
    if _cmd(r"mkfs(\.(ext[234]|xfs|btrfs|fat|vfat|ntfs|reiserfs|jfs|f2fs|minix|swap))?", s):
        return "格式化文件系统"
    if _has(r"\bchmod\s+-?R?\s*0?777\b", s) or (_cmd("chmod", s) and _has(r"(^|\s)-\S*R", s, sensitive=True) and _has(r"\s(/|~)(\s|/|$)", s)):
        return "递归/全开 chmod,可能破坏权限"
    if _has(r"\bchmod\s+(-\S+\s+)*0{3,4}\b", s):
        return "chmod 000 清空权限,文件将不可访问"
    for command in ("chown", "chgrp"):
        if _cmd(command, s) and _has(r"(^|\s)-\S*R", s, sensitive=True) and _has(r"\s(/|~)(\s|/|$)", s):
            return f"递归 {command} 到根/家目录"
    if _has(r">\s*/etc/", s):
        return "覆盖 /etc 系统配置"
    if _has(r"(^|\s):?\s*>\s*(/(etc|dev|bin|usr|boot|lib|sbin|var)/|~/|\$home)", _DEV_NULL.sub("", s)):
        return "重定向截断系统/家目录文件"
    target = re.search(r"\s((?:/|~)\S*)", s, re.IGNORECASE | re.ASCII)
    if _cmd("truncate", s) and target and not _has(r"^/(?:var/)?tmp/", target[1]):
        return "truncate 截断文件(可能清空数据)"
    if _cmd("shred", s):
        return "shred 不可逆抹除文件"
    if _cmd("find", s) and _has(r"(^|\s)-delete\b|(^|\s)-exec\s+(sudo\s+)?rm\b", s):
        return "find 批量删除(-delete/-exec rm)"
    if _cmd("git", s):
        if _has(r"\bpush\b", s) and _has(r"(--force(-with-lease)?|(^|\s)-f)\b", s):
            return "git push 强推,可能覆盖远程历史"
        if _has(r"\breset\b", s) and _has(r"--hard\b", s):
            return "git reset --hard,丢弃未提交改动"
        if _has(r"\bclean\b", s) and _has(r"(^|\s)-\S*f", s) and _has(r"(^|\s)-\S*[dx]", s):
            return "git clean -fdx,删除未跟踪文件"
    if _has(r"(^|\s)kill(?=\s|$|;|&|\|)\s+(-9\s+)?-1\b", s):
        return "kill -1/-9 -1,杀光本用户所有进程"
    if _cmd("killall", s):
        return "killall 批量杀进程"
    if _cmd("pkill", s) and _has(r"(^|\s)-9\b", s):
        return "pkill -9 强杀进程"
    if _cmd("sudo", s):
        return "sudo 提权"
    if _cmd("eval", s):
        return "eval 动态执行"
    return None


def isDangerousCommand(command: str) -> str | None:
    if not command.strip():
        return None
    if _has(r"\b(curl|wget|fetch)\b[\s\S]*\|\s*(sudo\s+)?(sh|bash|zsh|fish|python|perl|node|ruby)\b", command):
        return "下载内容直接管道执行(远程代码执行风险)"
    if re.search(r":\(\)\{:\|:&\};:", re.sub(r"\s", "", command)):
        return "fork bomb(耗尽进程)"
    for segment in splitBashCommands(command):
        reason = _dangerSegment(segment.strip())
        if reason:
            return reason
    return None


def isReadOnlyShellCommand(command: str) -> bool:
    s = command.strip()
    if not s or isDangerousCommand(s):
        return False
    sansDevNull = _DEV_NULL.sub("", s)
    if re.search(r"<|>|`", sansDevNull) or "$(" in s or "||" in s or "&" in sansDevNull.replace("&&", ""):
        return False
    segments = [part.strip() for part in re.split(r";|\n|&&|\|", s) if part.strip()]
    if not segments:
        return False
    for segment in segments:
        tokens = re.split(r"\s+", segment)
        command = tokens[0].rsplit("/", 1)[-1]
        if command == "git":
            if len(tokens) < 2 or tokens[1] not in _GIT:
                return False
        elif command == "find":
            if _has(r"(^|\s)-(delete|exec|execdir|ok|okdir|fprint|fprintf|fls)\b", segment, sensitive=True):
                return False
        elif command not in _READONLY:
            return False
    return True
