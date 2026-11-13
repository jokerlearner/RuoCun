"""从冻结 harbor_dao_agent.py（MIT）迁移的 Harbor / Terminal-Bench Python 入口。"""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

try:
    from harbor.agents.installed.base import BaseInstalledAgent, with_prompt_template
    from harbor.environments.base import BaseEnvironment
    from harbor.models.agent.context import AgentContext
    from harbor.models.trial.paths import EnvironmentPaths
except ImportError as error:
    raise RuntimeError("environment_unavailable: 需要与目标 Terminal-Bench 兼容的 Harbor。") from error

_AGENT_DIR = EnvironmentPaths.agent_dir.as_posix()


class RuoCunAgent(BaseInstalledAgent):
    @staticmethod
    def name() -> str:
        return "ruocun"

    def __init__(self, *args: Any, python: str = "python3", model: str = "",
                 config: str = "", progress_advice: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._python, self._model, self._config = python, model, config
        self._progress_advice = progress_advice

    def get_version_command(self) -> str:
        return shlex.join((self._python, "-m", "ruocun", "--version"))

    async def install(self, environment: BaseEnvironment) -> None:
        probe = (Path(__file__).resolve().parents[2] / "runtime_probe.py").read_text(encoding="utf-8")
        command = shlex.join((self._python, "-I", "-c", probe))
        result = await self.exec_as_agent(environment, command=command)
        if result.return_code != 0:
            raise RuntimeError("environment_unavailable: 任务环境无法加载 RuoCun 普通入口所需的受控 SQLite。")

    @with_prompt_template
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        if not self._config.startswith("/"):
            raise RuntimeError("environment_unavailable: 缺少显式任务账户或模型凭据。")
        argv = [self._python, "-m", "ruocun", "--eval", "--no-hooks", "--no-skills", "--config", self._config]
        if self._model:
            argv.extend(("--model", self._model))
        if self._progress_advice:
            argv.append("--progress-advice")
        argv.extend(("--", instruction))
        env = {"RUOCUN_DECK": "0", "RUOCUN_NO_NOTIFY": "1", "RUOCUN_AUTO_APPROVE": "1",
               "RUOCUN_USE_KEYCHAIN": "0"}
        logfile = shlex.quote(f"{_AGENT_DIR}/ruocun_stdout.txt")
        result = await self.exec_as_agent(environment, command=f"{shlex.join(argv)} > {logfile} 2>&1", env=env)
        if result.return_code != 0:
            raise RuntimeError(f"agent_error: RuoCun 退出码 {result.return_code}，见受控任务日志。")

    def populate_context_post_run(self, context: AgentContext) -> None:
        # Only the independent Harbor verifier assigns a benchmark reward.
        return
