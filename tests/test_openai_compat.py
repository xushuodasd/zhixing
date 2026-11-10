"""OpenAICompatProvider 离线测试：请求构造、响应解析与错误折算。

全部用例经 ``httpx.MockTransport`` 运行，绝不发起真实网络请求。
"""

import json

import httpx
import pytest

from zhixing import (
    Message,
    OpenAICompatProvider,
    ProviderError,
    ToolCall,
    ToolRegistry,
    tool,
)


def _completion_json(message: dict[str, object], finish_reason: str = "stop") -> dict[str, object]:
    """构造最小合法的 chat completion 响应体。"""
    return {"choices": [{"message": message, "finish_reason": finish_reason}]}


def _capturing_provider(
    requests: list[httpx.Request],
    response_body: object,
) -> OpenAICompatProvider:
    """构造一个记录请求并固定响应的离线 Provider。"""

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=response_body)

    return OpenAICompatProvider(api_key="test-key", transport=httpx.MockTransport(handler))


def test_request_construction_url_auth_and_body() -> None:
    """请求方法/URL/鉴权头/消息体按 OpenAI 兼容形态构造。"""
    requests: list[httpx.Request] = []
    provider = _capturing_provider(
        requests, _completion_json({"role": "assistant", "content": "你好"})
    )
    response = provider.complete([Message.system("你是助手"), Message.user("你好")])

    assert response.message.content == "你好"
    assert response.finish_reason == "stop"
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://api.deepseek.com/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-key"
    body = json.loads(request.content)
    assert body["model"] == "deepseek-chat"
    assert body["messages"] == [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
    ]
    assert "tools" not in body
    provider.close()


def test_tools_schemas_passed_through() -> None:
    """ToolRegistry.schemas() 输出原样进入请求体 tools 字段。"""

    @tool
    def get_weather(city: str) -> str:
        """查询天气。"""
        return city

    registry = ToolRegistry()
    registry.register(get_weather)
    requests: list[httpx.Request] = []
    provider = _capturing_provider(
        requests, _completion_json({"role": "assistant", "content": "ok"})
    )

    provider.complete([Message.user("天气")], registry.schemas())

    body = json.loads(requests[0].content)
    assert body["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询天气。",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ]
    provider.close()


def test_tool_calls_serialized_to_json_string() -> None:
    """助手消息 tool_calls.arguments（dict）序列化为 JSON 字符串；tool 消息带 tool_call_id。"""
    requests: list[httpx.Request] = []
    provider = _capturing_provider(
        requests, _completion_json({"role": "assistant", "content": "ok"})
    )
    messages = [
        Message.assistant(
            tool_calls=[ToolCall(id="call-1", name="get_weather", arguments={"city": "北京"})]
        ),
        Message.tool("call-1", "晴"),
    ]

    provider.complete(messages)

    body = json.loads(requests[0].content)
    assert body["messages"] == [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": '{"city": "北京"}'},
                }
            ],
        },
        {"role": "tool", "content": "晴", "tool_call_id": "call-1"},
    ]
    provider.close()


def test_response_tool_calls_deserialized() -> None:
    """响应中的 tool_calls.arguments（JSON 字符串）反序列化为 dict。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_completion_json(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-9",
                            "type": "function",
                            "function": {"name": "get_weather", "arguments": '{"city": "北京"}'},
                        }
                    ],
                },
                finish_reason="tool_calls",
            ),
        )

    provider = OpenAICompatProvider(api_key="k", transport=httpx.MockTransport(handler))
    response = provider.complete([Message.user("天气")])

    assert response.finish_reason == "tool_calls"
    assert response.message.role == "assistant"
    assert response.message.content is None
    assert response.message.tool_calls == [
        ToolCall(id="call-9", name="get_weather", arguments={"city": "北京"})
    ]
    provider.close()


def test_non_2xx_becomes_provider_error_without_key_leak() -> None:
    """非 2xx → ProviderError（含状态码与摘要，绝不含密钥）。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="auth failed")

    provider = OpenAICompatProvider(
        api_key="secret-key-123", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(ProviderError) as exc_info:
        provider.complete([Message.user("hi")])

    assert "401" in str(exc_info.value)
    assert "auth failed" in str(exc_info.value)
    assert "secret-key-123" not in str(exc_info.value)
    provider.close()


def test_timeout_becomes_provider_error() -> None:
    """超时 → ProviderError。"""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("connect timed out", request=request)

    provider = OpenAICompatProvider(
        api_key="k", timeout=0.5, transport=httpx.MockTransport(handler)
    )
    with pytest.raises(ProviderError, match="超时"):
        provider.complete([Message.user("hi")])
    provider.close()


def test_malformed_response_becomes_provider_error() -> None:
    """缺 choices / 非 JSON 响应体 → ProviderError。"""

    def empty_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    provider = OpenAICompatProvider(api_key="k", transport=httpx.MockTransport(empty_handler))
    with pytest.raises(ProviderError, match="choices"):
        provider.complete([Message.user("hi")])
    provider.close()

    def text_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    provider2 = OpenAICompatProvider(api_key="k", transport=httpx.MockTransport(text_handler))
    with pytest.raises(ProviderError, match="JSON"):
        provider2.complete([Message.user("hi")])
    provider2.close()


def test_invalid_tool_call_arguments_become_provider_error() -> None:
    """响应中 tool_calls.arguments 非法 JSON → ProviderError。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_completion_json(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "c1",
                            "type": "function",
                            "function": {"name": "x", "arguments": "{oops"},
                        }
                    ],
                }
            ),
        )

    provider = OpenAICompatProvider(api_key="k", transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError, match="JSON"):
        provider.complete([Message.user("hi")])
    provider.close()


def test_unserializable_arguments_become_provider_error() -> None:
    """请求侧 tool_calls.arguments 不可 JSON 序列化 → ProviderError。"""
    requests: list[httpx.Request] = []
    provider = _capturing_provider(
        requests, _completion_json({"role": "assistant", "content": "ok"})
    )
    messages = [Message.assistant(tool_calls=[ToolCall(id="c", name="t", arguments={"x": {1, 2}})])]

    with pytest.raises(ProviderError, match="序列化"):
        provider.complete(messages)

    assert requests == []  # 请求未发出
    provider.close()


def test_api_key_from_env_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    """无显式 api_key 时：ZHIXING_API_KEY 优先于 OPENAI_API_KEY。"""
    monkeypatch.setenv("OPENAI_API_KEY", "from-openai")
    monkeypatch.setenv("ZHIXING_API_KEY", "from-zhixing")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_completion_json({"role": "assistant", "content": "ok"}))

    provider = OpenAICompatProvider(transport=httpx.MockTransport(handler))

    provider.complete([Message.user("hi")])

    assert requests[0].headers["Authorization"] == "Bearer from-zhixing"
    provider.close()


def test_api_key_falls_back_to_openai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """只设置 OPENAI_API_KEY 时回退可用。"""
    monkeypatch.delenv("ZHIXING_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "from-openai")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_completion_json({"role": "assistant", "content": "ok"}))

    provider = OpenAICompatProvider(transport=httpx.MockTransport(handler))

    provider.complete([Message.user("hi")])

    assert requests[0].headers["Authorization"] == "Bearer from-openai"
    provider.close()


def test_missing_api_key_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    """入参与环境变量都缺失时，构造即抛 ProviderError。"""
    monkeypatch.delenv("ZHIXING_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ProviderError, match="API Key"):
        OpenAICompatProvider()


def test_context_manager_closes_client() -> None:
    """支持 with 语法：退出即关闭底层连接。"""
    with OpenAICompatProvider(api_key="k") as provider:
        assert provider._client.is_closed is False
    assert provider._client.is_closed is True
