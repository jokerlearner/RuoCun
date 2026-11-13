"""index.ts:2251–2266 的窗口命令解析，必要的 Python 提取确认（MIT）。"""

import pytest

from ruocun.session.context_window import parseContextWindow


@pytest.mark.parametrize(("argument", "expected"), [("200K", 200_000), ("1M", 1_000_000), ("500", 500_000)])
def test_source_command_examples(argument: str, expected: float):
    assert parseContextWindow(argument) == expected


def test_decimal_suffix_and_source_rejections():
    assert parseContextWindow("1.5m") == 1_500_000
    with pytest.raises(ValueError, match="无效格式"):
        parseContextWindow("oops")
    with pytest.raises(ValueError, match="最小 1K"):
        parseContextWindow("0.5K")
