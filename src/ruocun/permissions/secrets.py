"""为权限流程复用统一的秘密扫描入口。"""
from ..memory.secrets import findSecrets as findSecrets
from ..memory.secrets import redactSecrets as redactSecrets
