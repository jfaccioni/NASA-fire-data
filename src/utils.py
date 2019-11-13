from pandas import options


def ignore_pandas_warning(func):
    def f(*args, **kwargs):
        options.mode.chained_assignment = None
        return_value = func(*args, **kwargs)
        options.mode.chained_assignment = 'warn'
        return return_value
    return f
