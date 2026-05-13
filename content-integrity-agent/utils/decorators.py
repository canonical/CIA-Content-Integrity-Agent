import functools
import random
import time


def retry(max_attempts: int = 3, backoff_factor: float = 1.0, jitter: bool = True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        delay = backoff_factor * (2 ** (attempt - 1))
                        if jitter:
                            delay *= (0.5 + random.random())
                        time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator
