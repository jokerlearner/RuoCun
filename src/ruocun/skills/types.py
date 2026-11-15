"""定义加载、展示和执行技能时共用的记录字段。"""

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
