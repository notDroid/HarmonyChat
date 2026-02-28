from typing import Protocol, Callable, Any

class TaskQueue(Protocol):
    """
    Framework-agnostic interface for scheduling background work.
    """
    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        ...