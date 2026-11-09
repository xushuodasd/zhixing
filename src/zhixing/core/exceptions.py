"""框架统一异常体系。

所有 zhixing 主动抛出的异常都继承 :class:`ZhixingError`，调用方只需捕获
基类即可与框架交互；细分异常用于标记错误的来源环节，便于 Agent 循环
区分"可向模型反馈后继续"（工具执行失败）与"应当终止本轮"（超出迭代
上限、Provider 调用失败）等情况。
"""

from __future__ import annotations


class ZhixingError(Exception):
    """zhixing 框架异常基类，覆盖配置、校验与运行期错误。"""


class ProviderError(ZhixingError):
    """模型服务（Provider）调用失败：网络、鉴权或响应格式不符合预期。"""


class ToolExecutionError(ZhixingError):
    """工具执行失败：查无工具、参数不合法或 handler 抛出异常。

    注意：:class:`~zhixing.tools.registry.ToolRegistry.execute` 的常规
    失败路径会把异常折算为 ``is_error=True`` 的工具结果而非抛出本异常；
    本异常供注册表之外的工具管理场景（如参数预校验）使用。
    """


class MaxIterationsError(ZhixingError):
    """Agent 规划-执行循环超出最大迭代次数仍未得出最终答案。"""
