#!/usr/bin/env python
"""Value conversion functions.

These are mostly used for converting string representations of values
(e.g. for users input, data from text files, etc.).

History:
2003-05-08 ROwen    Adapted from functions in KeyVariable.
2003-06-13 ROwen    Added asStr.
2004-03-05 ROwen    Added asASCII.
2004-09-01 ROwen    Added asBoolOrNone.
2005-05-10 ROwen    Added StrCnvNoCase.
2005-06-08 ROwen    Changed StrCnv and StrCnvNoCase to new style classes.
2008-03-13 ROwen    asBool: Added on/off to allowed boolean values.
"""
import SeqUtil

_FalseValues = set((False, 0, "0", "f", "false", "no", "off", None))
_TrueValues  = set((True,  1, "1", "t", "true",  "yes", "on"))
_BoolDict = {}
for val in _FalseValues:
    _BoolDict[val] = False
for val in _TrueValues:
    _BoolDict[val] = True

_NoneValues = (None, "?", "nan")
_BoolOrNoneDict = _BoolDict.copy()
for val in _NoneValues:
    _BoolOrNoneDict[val] = None

def asASCII(val):
    """Converts the argument to an ASCII string.
    Raises UnicodeDecodeError if the result would contain non-ASCII characters.
    """
    # The inner "str" converts objects with str representations to strings.
    # The outer str converts the unicode string to a normal string.
    return str(unicode(str(val), "ascii"))

def asBool(val):
    """Converts typical human-readable boolean values to True or False

    Valid values:
    returns False for: False, 0, "0", "f", "false", "no", None
    returns True for:  True,  1, "1", "t", "true",  "yes"
    
    String values are not case-sensitive.
    Due to the fact that 1.0 == 1 and 0.0 == 0, the floating point versions also work.

    Raises ValueError or TypeError for all other values
    """
    global _BoolDict
    if hasattr(val, "lower"):
        val = val.lower()
    try:
        return _BoolDict[val]
    except (KeyError, TypeError):
        raise ValueError, "%r is not a valid boolean" % (val,)

def asBoolOrNone(val):
    """Converts typical human-readable boolean values to True, False
    or None.
    
    Valid values:
    returns False for: False, 0, "0", "f", "false", "no"
    returns True for:  True,  1, "1", "t", "true",  "yes"
    returns None for:  None, "?", "NaN"
    
    String values are not case-sensitive.
    Due to the fact that 1.0 == 1 and 0.0 == 0, the floating point versions also work.

    Raises ValueError or TypeError for all other values
    """
    global _BoolOrNoneDict
    if hasattr(val, "lower"):
        val = val.lower()
    try:
        return _BoolOrNoneDict[val]
    except (KeyError, TypeError):
        raise ValueError, "%r is not a valid boolean" % (val,)

def asFloat(val):
    """Converts floats, integers and string representations of either to floats.

    Raises ValueError or TypeError for all other values
    """
    if hasattr(val, "lower") and val.lower() == "nan":
        raise ValueError("%s is not a valid float" % (val,))
    else:
        return float(val)

def asFloatOrNone(val):
    """Converts floats, integers and string representations of either to floats.
    If val is "NaN" (case irrelevant) returns None.

    Raises ValueError or TypeError for all other values
    """
    # check for NaN first in case ieee floating point is in use
    # (in which case float(val) would return something instead of failing)
    if hasattr(val, "lower") and val.lower() == "nan":
        return None
    else:
        return float(val)

class FloatOrNoneFromStr(object):
    """Convert a string to a float, or None if a bad value.
    
    Unlike asFloatOrNone:
    - The value is compared to a user-specified set of bad values
      (note that the comparison is case-blind).
    - Only strings (or string-like objects) are accepted as input.
      This is to avoid the problem of dealing with bad values
      that may be strings or may be numbers, and also to avoid comparing
      bad values that have no exact floating point representation.
    
    Inputs:
    - badStrs: a string or collection of strings representing bad values.
        Case is ignored.
    """
    def __init__(self, badStrs="NaN"):
        if not SeqUtil.isCollection(badStrs):
            self.badStrs = set([badStrs.lower()])
        else:
            self.badStrs = set([bs.lower() for bs in badStrs])
        
    def __call__(self, strVal):
        try:
            if strVal.lower() in self.badStrs:
                return None
        except AttributeError:
            raise TypeError("%r is not a string" % (strVal,))
        return float(strVal)

def asInt(val):
    """Converts floats, integers and string representations of integers
    (in any base) to integers. Truncates floats.

    Raises ValueError or TypeError for all other values
    """
    if hasattr(val, "lower"):
        # string-like object; force base to 0
        return int(val, 0)
    else:
        # not a string; convert as a number (base cannot be specified)
        return int(val)

def asIntOrNone(val):
    """Converts floats, integers and string representations of integers
    (in any base) to integers. Truncates floats.
    If val is "NaN" (case irrelevant) returns None.

    Raises ValueError or TypeError for all other values
    """
    if hasattr(val, "lower"):
        # string-like object; check for NaN and force base to 0
        if val.lower() == "nan":
            return None
        return int(val, 0)
    else:
        # not a string; convert as a number (base cannot be specified)
        return int(val)

class IntOrNoneFromStr(object):
    """Convert a string to an int, or None if a bad value.
    
    Unlike asIntOrNone:
    - The value is compared to a user-specified set of bad values
      (note that the comparison is case-blind).
    - Only strings (or string-like objects) are accepted as input.
      This is to avoid the problem of dealing with bad values
      that may be strings or may be numbers.
    
    Inputs:
    - badStrs: a string or collection of strings representing bad values.
        Case is ignored.
    """
    def __init__(self, badStrs="NaN"):
        if not SeqUtil.isCollection(badStrs):
            self.badStrs = set([badStrs.lower()])
        else:
            self.badStrs = set([bs.lower() for bs in badStrs])
        
    def __call__(self, strVal):
        try:
            if strVal.lower() in self.badStrs:
                return None
        except AttributeError:
            raise TypeError("%r is not a string" % (strVal,))
        return int(strVal)

def asStr(val):
    """Returns val converted to a string (str object) if possible,
    else returns a unicode string. Differs from str in that it
    does not choke on unicode strings.
    """
    try:
        return str(val)
    except ValueError:
        return unicode(val)

class StrCnv(object):
    """Similar to str but with an optional substitution dictionary.
    """
    def __init__(self, subsDict=None):
        """Inputs:
        - subsDict: a substitution dictionary;
          if the value to be converted matches any key (case matters)
          then the converted value is the associated value.
          Otherwise the value is returned unchanged.
        """
        self.subsDict = subsDict or {}

    def __call__(self, key):
        strKey = str(key)
        return self.subsDict.get(strKey, strKey)

class StrCnvNoCase(object):
    """Similar to str but with an optional case-insensitive substitution dictionary.
    """
    def __init__(self, subsDict=None):
        """Inputs:
        - subsDict: a substitution dictionary;
          if the value to be converted matches any key (case is ignored)
          then the converted value is the associated value.
          Otherwise the value is returned unchanged.
        """
        self.subsDict = {}
        if subsDict:
            for key, val in subsDict.iteritems():
                self.subsDict[key.lower()] = val

    def __call__(self, key):
        strKey = str(key)
        return self.subsDict.get(strKey.lower(), strKey)

def nullCnv(val):
    """Null converter"""
    return val

if __name__ == "__main__":
    import random
    import sys
    import RO.SysConst
    import RO.MathUtil
    print "running CnvUtil test"
    
    def tryFunc(func, arg, desVal):
        try:
            if isinstance(desVal, float):
                isOK = (RO.MathUtil.compareFloats(func(arg), desVal) == 0)
            else:
                isOK = (func(arg) == desVal)
            if not isOK:
                print "error: %s(%r) != %r" % (funcName(func), arg, desVal)
        except StandardError, e:
            print "error: %s(%r) failed with: %s" % (funcName(func), arg, e)
            
    def failFunc(func, arg):
        """Call to test arguments that should fail"""
        try:
            junk = func(arg)
            print "error: %s(%r) = %r but should raise ValueError" % \
                (funcName(func), arg, junk)
        except (ValueError, TypeError):
            pass
        except StandardError, e:
            print "%s(%r) should have raised ValueError or TypeError, but raised %s = %s" % \
                (funcName(func), arg, e.__class__.__name__, e)
    
    def funcName(func):
        """Returns the name of a function or class"""
        try:
            return func.__name__
        except AttributeError:
            return func.__class__.__name__
            
    func = asBool
    print "testing %s" % (funcName(func),)

    for val in _FalseValues:
        tryFunc(func, val, False)
        if hasattr(val, "upper"):
            tryFunc(func, val.upper(), False)
    for val in _TrueValues:
        tryFunc(func, val, True)
        if hasattr(val, "upper"):
            tryFunc(func, val.upper(), True)

    for badVal in ("NaN", "NAN", "hello", 2, -1, (), [], {}, object):
        failFunc(func, badVal)


    func = asFloat
    print "testing %s" % (funcName(func),)

    for ii in range(1000):
        floatVal = (random.random() - 0.5) * 2.0 * RO.SysConst.FBigNum
        tryFunc(func, floatVal, floatVal)
        tryFunc(func, str(floatVal), floatVal)

    for badVal in ("NaN", "NAN", "hello", (), [], {}, object):
        failFunc(func, badVal)

    
    func = asFloatOrNone
    print "testing %s" % (funcName(func),)

    for ii in range(1000):
        floatVal = (random.random() - 0.5) * 2.0 * RO.SysConst.FBigNum
        tryFunc(func, floatVal, floatVal)
        tryFunc(func, str(floatVal), floatVal)
    tryFunc(func, "NaN", None)
    tryFunc(func, "NAN", None)

    for badVal in ("hello", "1.2.3", (), [], {}, object):
        failFunc(func, badVal)

    
    BadFloatStr = "9999.9"
    func = FloatOrNoneFromStr(["NaN", BadFloatStr])
    print "testing %s" % (funcName(func),)

    for ii in range(1000):
        floatVal = (random.random() - 0.5) * 2.0 * RO.SysConst.FBigNum
        if str(floatVal) == BadFloatStr:
            continue
        tryFunc(func, str(floatVal), floatVal)
    tryFunc(func, "NaN", None)
    tryFunc(func, "NAN", None)
    tryFunc(func, BadFloatStr, None)

    for badVal in ("hello", "1.2.3", (), [], {}, object):
        failFunc(func, badVal)

    
    func = asInt
    print "testing %s" % (funcName(func),)
    for ii in range(1000):
        intVal = random.randint(-sys.maxint+1, sys.maxint-1)
        tryFunc(func, intVal, intVal)
        tryFunc(func, str(intVal), intVal)

    for badVal in ("NaN", "NAN", "hello", "1.2", (), [], {}, object):
        failFunc(func, badVal)

    
    func = asIntOrNone
    print "testing %s" % (funcName(func),)
    for ii in range(1000):
        intVal = random.randint(-sys.maxint+1, sys.maxint-1)
        tryFunc(func, intVal, intVal)
        tryFunc(func, str(intVal), intVal)
    tryFunc(func, "NaN", None)
    tryFunc(func, "NAN", None)

    for badVal in ("hello", "1.2", (), [], {}, object):
        failFunc(func, badVal)

    
    BadIntStr = "9999"
    func = IntOrNoneFromStr(["NaN", BadIntStr])
    print "testing %s" % (funcName(func),)
    for ii in range(1000):
        intVal = random.randint(-sys.maxint+1, sys.maxint-1)
        tryFunc(func, str(intVal), intVal)
    tryFunc(func, "NaN", None)
    tryFunc(func, "NAN", None)
    tryFunc(func, BadIntStr, None)

    for badVal in ("hello", "1.2", (), [], {}, object):
        failFunc(func, badVal)
