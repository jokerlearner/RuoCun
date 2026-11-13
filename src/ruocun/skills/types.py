"""冻结skills/skills.ts的共享Skill记录（MIT），保持原协议字段名。"""

from typing import TypedDict


class Skill(TypedDict, total=False):
    name: str
    description: str
    whenToUse: str
    slug: str
    paths: list[str]
    namespace: str
    modelInvokable: bool
    userInvocable: bool
    body: str
    dir: str
    file: str
