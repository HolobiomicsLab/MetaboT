from abc import ABC, abstractmethod
from typing import Any


class ToolTemplate(ABC):

    @abstractmethod
    def __init__(self, **kwargs: Any):
        pass

    @abstractmethod
    def tool_func(self, Any) -> Any:
        pass
