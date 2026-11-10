"""``@tool`` 装饰器的 schema 推导测试：类型映射、必填/默认值与 docstring。"""

import pytest

from zhixing import Tool, tool
from zhixing.core.exceptions import ZhixingError


def test_schema_types_required_and_defaults() -> None:
    """四种受支持类型正确映射；带默认值的参数不进入 required。"""

    @tool
    def weather(city: str, days: int, threshold: float = 0.5, verbose: bool = False) -> str:
        """查询天气预报。"""
        return f"{city}/{days}/{threshold}/{verbose}"

    assert isinstance(weather, Tool)
    assert weather.name == "weather"
    assert weather.description == "查询天气预报。"
    assert weather.parameters == {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "days": {"type": "integer"},
            "threshold": {"type": "number"},
            "verbose": {"type": "boolean"},
        },
        "required": ["city", "days"],
    }


def test_no_params_schema() -> None:
    """无参数函数推导出空 properties 与空 required。"""

    @tool
    def ping() -> str:
        """连通性探测。"""
        return "pong"

    assert ping.name == "ping"
    assert ping.description == "连通性探测。"
    assert ping.parameters == {"type": "object", "properties": {}, "required": []}


def test_missing_docstring_yields_empty_description() -> None:
    """无 docstring 时 description 为空字符串且不报错。"""

    @tool
    def echo(text: str) -> str:
        return text

    assert echo.description == ""
    assert echo.handler(text="hi") == "hi"


def test_handler_remains_callable() -> None:
    """装饰后 handler 保持原函数行为，默认值生效。"""

    @tool
    def add(a: int, b: int = 2) -> int:
        """整数相加。"""
        return a + b

    assert add.handler(a=1) == 3
    assert add.handler(a=1, b=5) == 6


def test_unsupported_annotation_rejected() -> None:
    """不受支持的类型标注（如 list[str]）在装饰期快速失败。"""
    with pytest.raises(ZhixingError, match="items"):

        @tool
        def bad(items: list[str]) -> str:
            """不支持 list 标注。"""
            return ""


def test_missing_annotation_rejected() -> None:
    """参数缺少类型标注时快速失败，报错信息包含参数名。"""
    with pytest.raises(ZhixingError, match=r"参数 'x' 缺少类型标注"):

        @tool
        def bad(x) -> str:  # 刻意缺少标注以触发校验
            """缺少标注。"""
            return ""


def test_var_args_rejected() -> None:
    """*args / **kwargs 在装饰期被拒绝。"""
    with pytest.raises(ZhixingError, match=r"可变参数 'parts'"):

        @tool
        def bad(*parts: str) -> str:
            """可变参数不支持。"""
            return ""

    with pytest.raises(ZhixingError, match=r"可变参数 'options'"):

        @tool
        def bad_kwargs(**options: bool) -> str:
            """关键字可变参数不支持。"""
            return ""
