"""固定Windows x64运行库资产的wheel标签；Hatchling 1.33公共build hook。"""

from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if self.target_name == "wheel":
            build_data["pure_python"] = False
            build_data["tag"] = "py311-none-win_amd64"
