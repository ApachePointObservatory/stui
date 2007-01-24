"""From Scott David Daniels <http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52549>.
My changes include:
- Used a name suggested by Eric Brunel
- Created a simpler and faster class that does not handle initial keyword arguments
- Created a factory function to return the fastest callable object.

History:
2002-12-20 ROwen    Bug fix: due to a typo, _GC would fail if keyword arguments were used
                    both initially and in the final call. Thanks to pychecker for finding this.
"""
def GenericCallback(callback, *firstArgs, **firstKWArgs):
    """Returns a callable object that when called with (*args, **kwArgs),
    calls a callback function with arguments: (*(firstArgs + args), **allKWArgs),
    where allKWArgs = firstKWArgs updated with kwArgs
    
    Note that if a given keyword argument is specified both at instantiation
    (in firstKWArgs) and when the object is called (in kwArgs),
    the value in the call (kwArgs) is used. No warning is issued.
    """
    if firstKWArgs:
        return _GC(callback, *firstArgs, **firstKWArgs)
    else:
        return _GCNoKWArgs(callback, *firstArgs)


class _GC:
    """The most generic callback class."""
    def __init__(self, callback, *firstArgs, **firstKWArgs):
        self.__callback = callback
        self.__firstArgs = firstArgs
        self.__firstKWArgs = firstKWArgs

    def __call__(self, *args, **kwArgs):
        if kwArgs:
            netKWArgs = self.__firstKWArgs.copy()
            netKWArgs.update(kwArgs)
        else:
            netKWArgs = self.__firstKWArgs 
        return self.__callback (*(self.__firstArgs + args), **netKWArgs)


class _GCNoKWArgs:
    """A callback class optimized for the case of no stored keyword args.
    This is a common case and should run faster than the more general case.
    """
    def __init__(self, callback, *firstArgs):
        self.__callback = callback
        self.__firstArgs = firstArgs

    def __call__(self, *args, **kwArgs):
        return self.__callback (*(self.__firstArgs + args), **kwArgs)

