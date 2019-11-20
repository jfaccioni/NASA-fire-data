from typing import Any, Callable

from pandas import options


def ignore_pandas_warning(func: Callable) -> Callable:
    """Decorator that ignores pandas SettingWithCopyWarning during the decorated function's execution"""
    def f(*args, **kwargs) -> Any:
        """Placeholder for the function called by the ignore_pandas_warning decorator"""
        options.mode.chained_assignment = None
        return_value = func(*args, **kwargs)
        options.mode.chained_assignment = 'warn'
        return return_value
    return f
