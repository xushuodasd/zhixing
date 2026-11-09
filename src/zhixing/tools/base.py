"""工具定义与声明式装饰器：把普通函数变成模型可调用的工具。

一个工具 = 元数据（名称 / 用途 / 参数 schema）+ 执行函数。
:func:`tool` 装饰器负责从函数的签名与 docstring 自动推导元数据，
让"定义一个工具"收敛为一行装饰器加一个带标注的函数。
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import get_type_hints

from zhixing.core.exceptions import ZhixingError

#: Python 标量类型到 JSON Schema 类型名的映射（本装饰器支持的全体类型）。
_PY_TO_JSON_TYPE: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


@dataclass
class Tool:
    """一个可被模型调用的工具。

    Attributes:
        name: 工具名，注册表内唯一。
        description: 给模型看的用途说明（通常取自函数 docstring）。
        parameters: 参数的 JSON Schema，``{"type": "object", ...}`` 形态。
        handler: 实际执行函数；注册表按 ``handler(**arguments)`` 调用。
    """

    name: str
    description: str
    parameters: dict[str, object]
    handler: Callable[..., object]


def tool(func: Callable[..., object]) -> Tool:
    """把普通函数声明为 :class:`Tool`（``@tool`` 装饰器用法）。

    推导规则：

    - ``name``：函数名；
    - ``description``：函数 docstring（缺失则为空字符串）；
    - ``parameters``：由函数签名推导的 JSON Schema，支持 ``str`` / ``int`` /
      ``float`` / ``bool`` 标注；带默认值的参数不进入 ``required``；
    - ``handler``：原函数，保持可调用。

    Args:
        func: 待转换的普通函数。

    Returns:
        转换后的 :class:`Tool` 实例（装饰后的名字指向 Tool，而非原函数）。

    Raises:
        ZhixingError: 参数缺少类型标注、标注类型不受支持，或出现
            ``*args`` / ``**kwargs`` 时抛出（装饰期快速失败）。
    """
    name = func.__name__
    description = inspect.getdoc(func) or ""
    signature = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception as exc:
        raise ZhixingError(f"无法解析工具 {name!r} 的类型标注：{exc}") from exc

    properties: dict[str, object] = {}
    required: list[str] = []
    for param_name, param in signature.parameters.items():
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            raise ZhixingError(f"工具 {name!r} 不支持可变参数 {param_name!r}（*args/**kwargs）")
        annotation = hints.get(param_name)
        if annotation is None:
            raise ZhixingError(
                f"工具 {name!r} 的参数 {param_name!r} 缺少类型标注（支持 str/int/float/bool）"
            )
        json_type = _PY_TO_JSON_TYPE.get(annotation)
        if json_type is None:
            raise ZhixingError(
                f"工具 {name!r} 的参数 {param_name!r} 类型 {annotation!r} 不受支持"
                "（支持 str/int/float/bool）"
            )
        properties[param_name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    parameters: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "required": required,
    }
    return Tool(name=name, description=description, parameters=parameters, handler=func)
