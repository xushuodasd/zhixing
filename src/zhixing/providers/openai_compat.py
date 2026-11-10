"""OpenAI 兼容 Provider：对接任意 OpenAI chat completions 兼容端点。

默认指向 DeepSeek 开放平台（``https://api.deepseek.com/v1``），国产模型
一等公民；任何兼容 OpenAI chat completions 协议的服务（DeepSeek、Kimi、
Qwen、vLLM 自部署等）只需换 ``base_url`` 与 ``model``。

请求/响应映射：

- :class:`~zhixing.core.types.Message` → OpenAI 消息对象；助手消息
  ``tool_calls.arguments`` 由 dict 序列化为 JSON 字符串；
- ``tools``（来自 :class:`~zhixing.tools.registry.ToolRegistry.schemas`）
  原样进入请求体 ``tools`` 字段（function calling 形态）；
- 响应中的 ``tool_calls.function.arguments``（JSON 字符串）反序列化回
  dict，封装为 :class:`~zhixing.core.types.ToolCall`。

错误语义：请求构造失败、网络错误、超时、非 2xx、响应格式不符合预期
一律抛出 :class:`~zhixing.core.exceptions.ProviderError`；错误信息只含
状态码与响应摘要，绝不包含 API Key。
"""

from __future__ import annotations

import json
import os
from typing import Self

import httpx

from zhixing.core.exceptions import ProviderError
from zhixing.core.types import Message, ProviderResponse, ToolCall

#: 缺省端点：DeepSeek 开放平台（OpenAI 兼容）。
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
#: api_key 未显式传入时依次尝试的环境变量。
API_KEY_ENV_VARS = ("ZHIXING_API_KEY", "OPENAI_API_KEY")
#: 缺省模型名（与缺省端点配套）。
DEFAULT_MODEL = "deepseek-chat"
#: 错误摘要中响应体的最大长度。
_BODY_SUMMARY_LIMIT = 300

_CHAT_COMPLETIONS_PATH = "/chat/completions"


def _resolve_api_key(api_key: str | None) -> str:
    """解析 API Key：显式传入优先，其次按序读取环境变量。

    Raises:
        ProviderError: 入参与环境变量都缺失时抛出（构造期快速失败）。
    """
    if api_key:
        return api_key
    for env_name in API_KEY_ENV_VARS:
        value = os.environ.get(env_name)
        if value:
            return value
    raise ProviderError(
        "未提供 API Key：请传入 api_key，或设置环境变量 ZHIXING_API_KEY / OPENAI_API_KEY"
    )


def _serialize_tool_call(call: ToolCall) -> dict[str, object]:
    """ToolCall → OpenAI tool_calls 条目（arguments dict → JSON 字符串）。"""
    return {
        "id": call.id,
        "type": "function",
        "function": {
            "name": call.name,
            "arguments": json.dumps(call.arguments, ensure_ascii=False),
        },
    }


def _serialize_message(message: Message) -> dict[str, object]:
    """Message → OpenAI 消息对象（仅携带该角色有意义的字段）。"""
    payload: dict[str, object] = {"role": message.role, "content": message.content}
    if message.tool_calls is not None:
        payload["tool_calls"] = [_serialize_tool_call(call) for call in message.tool_calls]
    if message.tool_call_id is not None:
        payload["tool_call_id"] = message.tool_call_id
    return payload


def _build_payload(
    model: str,
    messages: list[Message],
    tools: list[dict[str, object]] | None,
) -> dict[str, object]:
    """组装 OpenAI chat completions 请求体（空 tools 列表不下发）。"""
    payload: dict[str, object] = {
        "model": model,
        "messages": [_serialize_message(message) for message in messages],
    }
    if tools:
        payload["tools"] = list(tools)
    return payload


def _parse_tool_call(raw: object) -> ToolCall:
    """OpenAI tool_calls 条目 → ToolCall（arguments JSON 字符串 → dict）。"""
    if not isinstance(raw, dict):
        raise ProviderError("响应中的 tool_calls 条目不是对象")
    function = raw.get("function")
    if not isinstance(function, dict):
        raise ProviderError("响应中的 tool_calls 条目缺少 function 字段")
    raw_arguments = function.get("arguments")
    if raw_arguments in (None, ""):
        arguments: dict[str, object] = {}
    elif isinstance(raw_arguments, str):
        try:
            parsed = json.loads(raw_arguments)
        except ValueError as exc:
            raise ProviderError(f"tool_calls 的 arguments 不是合法 JSON：{exc}") from exc
        if not isinstance(parsed, dict):
            raise ProviderError("tool_calls 的 arguments 反序列化后不是对象")
        arguments = parsed
    else:
        raise ProviderError("tool_calls 的 arguments 必须是 JSON 字符串")
    call_id = raw.get("id")
    name = function.get("name")
    if not isinstance(call_id, str) or not isinstance(name, str):
        raise ProviderError("响应中的 tool_calls 缺少 id 或 function.name")
    return ToolCall(id=call_id, name=name, arguments=arguments)


def _parse_message(raw: object) -> Message:
    """OpenAI 响应 message 对象 → Message。"""
    if not isinstance(raw, dict):
        raise ProviderError("响应中的 message 不是对象")
    role = raw.get("role")
    if not isinstance(role, str):
        raise ProviderError("响应中的 message 缺少 role")
    content = raw.get("content")
    if content is not None and not isinstance(content, str):
        raise ProviderError("响应中的 message.content 不是字符串或 null")
    tool_calls: list[ToolCall] | None = None
    raw_tool_calls = raw.get("tool_calls")
    if raw_tool_calls is not None:
        if not isinstance(raw_tool_calls, list):
            raise ProviderError("响应中的 tool_calls 不是数组")
        tool_calls = [_parse_tool_call(item) for item in raw_tool_calls]
    return Message(role=role, content=content, tool_calls=tool_calls)


def _parse_response(data: object) -> ProviderResponse:
    """OpenAI chat completion 响应体 → ProviderResponse。"""
    if not isinstance(data, dict):
        raise ProviderError("响应体不是 JSON 对象")
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderError("响应缺少 choices（或为空）")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ProviderError("响应中的 choice 不是对象")
    finish_reason = choice.get("finish_reason")
    if finish_reason is not None and not isinstance(finish_reason, str):
        raise ProviderError("响应中的 finish_reason 不是字符串或 null")
    message = _parse_message(choice.get("message"))
    return ProviderResponse(message=message, finish_reason=finish_reason)


class OpenAICompatProvider:
    """OpenAI 兼容 Provider（:class:`~zhixing.providers.base.Provider` 实现）。

    用法::

        provider = OpenAICompatProvider()  # DeepSeek 端点 + 环境变量中的 Key
        response = provider.complete([Message.user("你好")])

    也支持上下文管理器（退出时关闭底层连接）。
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """初始化 Provider 并建立底层 HTTP 客户端。

        Args:
            base_url: OpenAI 兼容端点根地址（默认 DeepSeek 开放平台）。
            model: 模型名（默认 ``deepseek-chat``）。
            api_key: API Key；缺省时依次读取环境变量
                ``ZHIXING_API_KEY`` / ``OPENAI_API_KEY``，都缺失则抛出
                :class:`ProviderError`。
            timeout: 单次请求超时（秒）。
            transport: 可选的 httpx 传输层；测试时注入
                ``httpx.MockTransport`` 以完全离线运行。
        """
        self._base_url = base_url
        self._model = model
        self._timeout = timeout
        self._api_key = _resolve_api_key(api_key)
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=timeout,
            transport=transport,
        )

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, object]] | None = None,
    ) -> ProviderResponse:
        """执行一次对话补全；一切失败折算为 :class:`ProviderError`。"""
        try:
            payload = _build_payload(self._model, messages, tools)
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"请求构造失败（参数可能不可 JSON 序列化）：{exc}") from exc
        try:
            response = self._client.post(_CHAT_COMPLETIONS_PATH, json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderError(
                f"模型请求超时（timeout={self._timeout}s）：{type(exc).__name__}: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"模型请求失败：{type(exc).__name__}: {exc}") from exc
        if not response.is_success:
            summary = response.text[:_BODY_SUMMARY_LIMIT]
            raise ProviderError(f"模型服务返回 HTTP {response.status_code}：{summary}")
        try:
            data: object = response.json()
        except ValueError as exc:
            summary = response.text[:_BODY_SUMMARY_LIMIT]
            raise ProviderError(
                f"响应体不是合法 JSON（HTTP {response.status_code}）：{summary}"
            ) from exc
        return _parse_response(data)

    def close(self) -> None:
        """关闭底层 HTTP 连接。"""
        self._client.close()

    def __enter__(self) -> Self:
        """进入上下文管理器，返回自身。"""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """退出上下文管理器时关闭底层连接。"""
        self.close()
