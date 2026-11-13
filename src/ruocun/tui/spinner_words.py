"""冻结tui/spinner_words.ts（MIT）的道家动词。"""

SPINNER_WORDS = ["悟", "观", "参", "思", "究", "玩", "酌", "衡", "推", "索", "凝", "省", "察", "度", "游", "化", "涤", "虚"]


def spinner_word(index: int) -> str:
    return SPINNER_WORDS[index % len(SPINNER_WORDS)]
