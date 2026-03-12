"""Base class for Skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from kweaver._errors import (
    ADPError,
    AuthenticationError,
    AuthorizationError,
    ServerError,
)

if TYPE_CHECKING:
    from kweaver._client import ADPClient


class BaseSkill(ABC):
    def __init__(self, client: ADPClient) -> None:
        self.client = client

    @abstractmethod
    def _execute(self, **kwargs: Any) -> dict[str, Any]: ...

    def run(self, **kwargs: Any) -> dict[str, Any]:
        try:
            return self._execute(**kwargs)
        except AuthorizationError as e:
            return {"error": True, "message": f"当前账号无权执行此操作: {e.message}"}
        except AuthenticationError as e:
            return {"error": True, "message": f"认证失败: {e.message}"}
        except ServerError as e:
            trace = f" (trace: {e.trace_id})" if e.trace_id else ""
            return {"error": True, "message": f"ADP 服务异常{trace}，请稍后重试"}
        except ADPError as e:
            return {"error": True, "message": e.message}
