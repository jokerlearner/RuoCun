"""Eval configuration, using the same explicit-account boundary as ticket 72."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from ruocun.client.client import streamChat
from ruocun.client.types import StreamChatOptions

from ...local_model import localTransport
from ...run import EnvironmentIssue, _profile


class InvalidEvaluation(ValueError):
    """Model or fixture material cannot be scored."""


@dataclass(frozen=True, repr=False)
class EvalConfig:
    options: StreamChatOptions
    judgeK: int
    mode: str

    async def call(self, options: StreamChatOptions) -> str:
        transport = None if self.mode == "live" else localTransport
        try:
            response = await asyncio.to_thread(streamChat, options, transport=transport, env={})
        except Exception:
            raise EnvironmentIssue("模型入口请求失败。") from None
        value = response.message.get("content")
        if response.status != "complete" or not isinstance(value, str) or not value.strip():
            raise InvalidEvaluation("模型响应不完整。")
        return value


def loadEvalConfig(config: Path, *, live: bool, judge_k: int) -> EvalConfig:
    if judge_k < 1:
        raise EnvironmentIssue("judge 次数必须大于 0。")
    profiles, _ = _profile(config, live=live)
    active = profiles["profiles"]["eval"]
    options: StreamChatOptions = {"baseUrl": active["baseUrl"], "apiKey": active["key"],
                                  "model": os.environ.get("DEEPSEEK_MODEL") or active["model"],
                                  "provider": active["provider"], "messages": [], "maxRetries": 0,
                                  "idleTimeoutMs": 15000}
    return EvalConfig(options, judge_k, "live" if live else "offline")
