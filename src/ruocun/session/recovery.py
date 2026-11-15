"""恢复已中断会话，补齐已知工具结果并接受用户提供的恢复证据。

Shell 管理器先核实仍可接管的 runner，之后本模块装载后台状态。旧操作的结果仍未知时保留未决，用户授权继续代理时才派发新运行。
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .contract import (
    RecoveryDecision,
    RunRecord,
    RunRef,
    StoreError,
    ToolRecord,
    ToolRef,
)
from .sqlite_port import CommitUnconfirmedError, RollbackError

if TYPE_CHECKING:
    from ..agent.background_runtime import BackgroundRuntime
    from ..tools.managed_shell import ManagedShellManager
    from .conversation import Conversation
    from .session import Session


def attachmentToolRef(path: str) -> ToolRef:
    token = base64.urlsafe_b64encode(path.encode('utf-8')).decode('ascii').rstrip('=')
    return ToolRef('recovery', 'attachment:' + token)


def repairToolPairs(
    messages: Sequence[dict[str, Any]], records: Sequence[ToolRecord] | None = None,
    scope: str = 'main',
) -> list[dict[str, Any]]:
    """保留助手消息及已知结果，为缺失结果补一条说明，并标明原操作未自动重放。"""
    by_id = {record.tool_ref.tool_call_id: record for record in records or () if record.tool_ref.scope == scope}
    output: list[dict[str, Any]] = []
    index = 0
    while index < len(messages):
        message = copy.deepcopy(messages[index])
        index += 1
        output.append(message)
        calls = message.get('tool_calls') if message.get('role') == 'assistant' else None
        if not calls:
            continue
        existing: dict[str, dict[str, Any]] = {}
        while index < len(messages) and messages[index].get('role') == 'tool':
            item = messages[index]
            existing[str(item.get('tool_call_id'))] = copy.deepcopy(item)
            index += 1
        for call in calls:
            call_id = call['id']
            record = by_id.get(call_id)
            if call_id in existing:
                output.append(existing[call_id])
            elif record is not None and record.state == 'result_committed' and record.result is not None:
                output.append(copy.deepcopy(record.result) if isinstance(record.result, dict) else
                              {'role': 'tool', 'tool_call_id': call_id, 'content': record.result})
            else:
                content = ('[恢复：结果未知] 操作可能已执行；必须先核实，禁止自动重试。'
                           if records is None or record is not None else
                           '[恢复：未执行] 此工具没有执行意图记录，未自动重放。')
                output.append({'role': 'tool', 'tool_call_id': call_id, 'content': content})
    return output


def isMutatingRecoveryCommand(line: str) -> bool:
    return line.strip().split(maxsplit=2)[:2] in [
        ['/recovery', 'resolve'], ['/recovery', 'decide'], ['/recovery', 'continue']]


@dataclass(frozen=True)
class AgentContinuation:
    decision_id: str
    previous: RunRecord
    new_run: RunRef
    instruction: str
    material: dict[str, Any]


ContinueAgent = Callable[[AgentContinuation], Awaitable[RunRecord]]
ValidateContinuation = Callable[[AgentContinuation], Awaitable[None]]
ActivateContinuation = Callable[[RunRef], Awaitable[None]]


class RecoveryController:
    def __init__(
        self, conversation: Conversation, session: Session, background: BackgroundRuntime,
        shell_manager: ManagedShellManager | None = None, *, continue_agent: ContinueAgent | None = None,
        validate_continuation: ValidateContinuation | None = None,
        activate_continuation: ActivateContinuation | None = None,
    ) -> None:
        self.conversation, self.session, self.background = conversation, session, background
        self.shell_manager, self.continue_agent = shell_manager, continue_agent
        self.validate_continuation = validate_continuation
        self.activate_continuation = activate_continuation

    async def recover(self) -> None:
        """等 Shell 管理器核实原 runner 后，再整理恢复状态并绑定后台会话。"""
        await self.conversation.worker.enqueue_prepare_recovery(
            self.shell_manager.recovery_errors if self.shell_manager is not None else None).wait()
        await self.background.bind()
        await self.conversation.refresh_recovery(self.session)

    async def command(self, line: str, *, decision_id: str | None = None) -> str | None:
        parts = line.strip().split()
        if not parts or parts[0] != '/recovery':
            return None
        view = await self.conversation.background_view()
        if len(parts) == 1:
            report = {
                'tasks': [{'taskId': run.run_ref.task_id, 'runId': run.run_ref.run_id,
                           'kind': run.kind, 'status': run.status, 'cancelRequested': run.cancel_requested,
                           'resolvedByUser': bool(run.snapshot.get('resolved_by_user')),
                           'evidence': run.snapshot.get('user_evidence'),
                           'recovery': run.snapshot.get('recovery')} for run in view.runs],
                'unresolved': [{'scope': record.tool_ref.scope, 'id': record.tool_ref.tool_call_id,
                                'tool': record.name, 'args': record.args} for record in view.tool_records
                               if record.state != 'result_committed'],
                'missingAttachments': list(view.missing_attachments),
                'decisions': list(view.decisions),
                'blocked': self.conversation.blocked,
            }
            return self.conversation.redact(json.dumps(report, ensure_ascii=False, indent=2)) + (
                '\n核实未决工具：/recovery resolve <scope> <toolCallId> <说明>'
                '\n核实执行：/recovery decide <taskId> <completed|failed|canceled> <证据>'
                '\n继续已中断代理：/recovery continue <taskId> <继续指令>')
        action = parts[1]
        if action == 'resolve' and len(parts) >= 5:
            _, _, scope, call_id, explanation = line.strip().split(maxsplit=4)
            target, status = scope + ':' + call_id, None
        elif action == 'decide' and len(parts) >= 5:
            _, _, target, status, explanation = line.strip().split(maxsplit=4)
        elif action == 'continue' and len(parts) >= 4:
            _, _, target, explanation = line.strip().split(maxsplit=3)
            status = None
        else:
            raise ValueError('恢复命令格式无效；输入 /recovery 查看用法。')
        identifier = decision_id or 'recovery-v1:' + hashlib.sha256(
            (self.conversation.session_id + '\0' + line.strip()).encode('utf-8')).hexdigest()
        next_ref = RunRef(target, str(uuid.uuid5(uuid.NAMESPACE_URL, identifier))) if action == 'continue' else None
        decision = RecoveryDecision(identifier, action, target, explanation, line.strip(), status, next_ref)  # type: ignore[arg-type]
        prior = next((entry for entry in view.decisions if entry.get('request', {}).get('decision_id') == identifier), None)
        continuation: AgentContinuation | None = None
        if action == 'continue' and prior is None:
            if self.continue_agent is None:
                raise ValueError('普通代理继续的真实dispatcher尚未装配（38/39/41）；未授权、未启动新执行，原现场保留。')
            if self.conversation.blocked or view.missing_attachments:
                raise ValueError('仍有未决操作或缺失附件，不能继续代理。')
            candidates = [run for run in view.runs if run.run_ref.task_id == target]
            if not candidates or candidates[-1].kind not in {'agent', 'fork'} or candidates[-1].status != 'interrupted':
                raise ValueError('只能继续已中断的普通代理；Shell/monitor/manual不会转换成代理。')
            run = candidates[-1]
            material = self._validate_agent_material(run)
            assert next_ref is not None
            continuation = AgentContinuation(identifier, run, next_ref, explanation, material)
            if self.validate_continuation is not None:
                await self.validate_continuation(continuation)
        try:
            if self.shell_manager is not None:
                async with self.shell_manager.recovery_decision_scope():
                    receipt = await self.conversation.commit_recovery(self.session, decision)
            else:
                receipt = await self.conversation.commit_recovery(self.session, decision)
        except (CommitUnconfirmedError, RollbackError):
            raise
        except StoreError as error:
            raise ValueError(str(error)) from error
        if continuation is not None and not receipt.replayed:
            # 继续执行的许可要先提交到数据库，再派发新的运行。
            # 派发后即便取消或结果未知，也用原身份核查，避免同一许可启动两次。
            self.conversation.blocked = True
            assert self.continue_agent is not None
            result = await self.continue_agent(continuation)
            if result.run_ref != continuation.new_run or result.kind != continuation.previous.kind:
                raise ValueError('继续执行器返回身份不符，保留已授权未知执行，禁止重试。')
            await self.conversation.publish_background(result, None)
        await self.background.bind()
        await self.conversation.refresh_recovery(self.session)
        if continuation is not None and not receipt.replayed and self.activate_continuation is not None:
            await self.activate_continuation(continuation.new_run)
        if action == 'continue':
            continued = next((run for run in (await self.conversation.background_view()).runs if run.run_ref == next_ref), None)
            if continued is None or continued.status == 'unknown':
                raise ValueError('继续许可已保存但执行结果未确认；同ID不会再次启动，保留现场。')
            assert next_ref is not None
            return f'已记录继续许可，新run: {next_ref.run_id}；状态: {continued.status}。'
        return '已记录恢复决定；未自动重放旧操作。请输入下一条指令。'

    @staticmethod
    def _validate_agent_material(run: RunRecord) -> dict[str, Any]:
        raw = run.snapshot.get('recovery_material')
        if run.kind == 'fork' and (not isinstance(raw, dict) or not all(raw.get(key) for key in (
                'parentContext', 'exactTools', 'trimPolicy', 'pathIsolation'))):
            raise ValueError('fork缺少原父上下文或精确工具等现场；保留原转录，未授权继续。')
        if not isinstance(raw, dict):
            raise ValueError('代理恢复材料不足，未启动新执行。')
        material = copy.deepcopy(raw)
        required = ('model', 'agentType', 'definitionVersion', 'worktree', 'messages', 'permissions', 'budget')
        if any(key not in material for key in required):
            raise ValueError('代理恢复材料不完整，禁止使用当前默认配置猜测恢复。')
        if (not all(isinstance(material[key], str) and material[key] for key in ('model', 'agentType', 'definitionVersion', 'worktree'))
                or material['agentType'] in {'explore', 'plan'}
                or not isinstance(material['messages'], list) or not material['messages']
                or not all(isinstance(message, dict) for message in material['messages'])
                or material['messages'][0].get('role') != 'system'
                or not isinstance(material['permissions'], dict)
                or not isinstance(material['budget'], (int, float, type(None)))
                or not Path(material['worktree']).is_dir()):
            raise ValueError('原模型/定义/工作目录/消息/权限/预算材料无效，未启动新执行。')
        return material
