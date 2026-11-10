"""Provider 模块：模型服务的协议与实现。

- :mod:`zhixing.providers.base`：:class:`Provider` 协议；
- :mod:`zhixing.providers.openai_compat`：OpenAI 兼容实现；
- :mod:`zhixing.providers.fake`：脚本化假模型（离线测试/演示）。
"""

from zhixing.providers.base import Provider
from zhixing.providers.fake import FakeProvider
from zhixing.providers.openai_compat import OpenAICompatProvider

__all__ = [
    "FakeProvider",
    "OpenAICompatProvider",
    "Provider",
]
