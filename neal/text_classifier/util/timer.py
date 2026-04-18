import time
import functools
from typing import Callable, Any

from util.logger import get_logger

logger = get_logger("timer")

TIMING_REGISTRY: dict[str, float] = {}


class Timer:

    def __init__(self, step_name: str) -> None:
        self.step_name = step_name
        self.start_time: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.elapsed = time.perf_counter() - self.start_time
        TIMING_REGISTRY[self.step_name] = self.elapsed
        logger.info(f"✓ {self.step_name} completed in {self.elapsed:.2f}s")


def timeit(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        step_name = func.__name__
        TIMING_REGISTRY[step_name] = elapsed
        logger.info(f"✓ {step_name} completed in {elapsed:.2f}s")
        return result

    return wrapper
