#!/usr/local/bin/python
"""Python language utilities by Russell Owen

History:
2003-11-19 ROwen
"""
def funcName(func):
    """Returns the name of a function or instance method;
    if the function is a callable object then returns the name of the object's class.
    """
    try:
        return func.__name__
    except AttributeError:
        pass
    try:
        return func.__class__.__name__
    except AttributeError:
        pass
    return repr(func)
