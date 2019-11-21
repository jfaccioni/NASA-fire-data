from contextlib import contextmanager
from typing import Any, Callable

from pandas import options


@contextmanager
def conditional_open(filename: str, mode: str, condition: bool) -> Optional[TextIOWrapper]:
    """Context manager for returning an open file or a None value, depending on the condition argument"""
    if not condition:
        yield None
    resource = open(filename, mode)
    try:
        yield resource
    finally:
        resource.close()


def ignore_pandas_warning(func: Callable) -> Callable:
    """Decorator that ignores pandas SettingWithCopyWarning during the decorated function's execution"""
    def f(*args, **kwargs) -> Any:
        """Placeholder for the function called by the ignore_pandas_warning decorator"""
        options.mode.chained_assignment = None
        return_value = func(*args, **kwargs)
        options.mode.chained_assignment = 'warn'
        return return_value
    return f
