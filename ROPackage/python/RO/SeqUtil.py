#!/usr/bin/env python
"""Utilities for non-string-like collections of objects.

The following definitions are used in this module:

* Collection: any non-string-like collection of objects,
such as set, list, tuple, dict or any iterable. Note that
a collection need not be bounded (since iterators and generators
need not terminate).

* Sequence: any non-string-like numerically indexable collection of objects,
such as list or tuple, but not including dict or set.

These utilities intentionally consider string-like objects
(e.g. str, unicode, UserString...) as single objects, not collections.

History:
2003-11-18 ROwen    Extracted from MathUtil and added oneOrNAsSeq
2004-05-18 ROwen    Bug fix: flatten was called flattenList in a few places.
2005-06-07 ROwen    Added isString.
2005-06-15 ROwen    Added isCollection and asSet.
                    Improved the test code (though still does not test all functions).
2005-06-27 ROwen    Fixed a nonfunctional assert statement in the test code.
2005-09-23 ROwen    Added get.
2006-01-11 ROwen    Added asCollection.
                    Redefined Collection to mean any non-string-like iterable
                    (adopting a test suggested by Michael Spencer on comp.lang.python).
                    Collection and Sequence are now defined in the module's doc string.
2007-04-24 ROwen    Changed Numeric to numpy in a doc string.
"""
import UserString
import RO.MathUtil
try:
    set
except NameError:
    from sets import Set as set

def asCollection(item):
    """Convert one or more items to a Collection.
    If item is Collection, returns it unchanged,
    else returns [item].
    """
    if isCollection(item):
        return item
    return [item]

def asList(item):
    """Convert one or more items to a list, returning a copy.
    If item is a Sequence, returns list(item),
    else returns [item].
    """
    if isSequence(item):
        return list(item)
    return [item]

def asSequence(item):
    """Convert one or more items to a Sequence,
    If item is already a Sequence, returns it unchanged,
    else returns [item].
    """
    if isSequence(item):
        return item
    return [item]

def asSet(item):
    """Convert one or more items to a set.
    Note: a string counts as one item.
    Warning: if any items are not hashable (and thus are not
    valid entries in sets), raises an exception.
    """
    if isCollection(item):
        return set(item)
    return set((item,))

def flatten(a):
    """Flatten an arbitrarily nested Sequence of Sequences.
    """
    if not isSequence(a):
        raise ValueError("Argument not a sequence: %s" % (a,))
    return _flatten(a)

def _flatten(a):
    """Iterative solver for flatten.
    """
    ret = []
    for ai in a:
        if isSequence(ai):
            ret += flatten(ai)
        else:
            ret.append(ai)
    return ret

def get(seq, ind, defVal=None):
    """Return seq[ind] if available, else defVal"""
    try:
        return seq[ind]
    except LookupError:
        return defVal

def isCollection(item):
    """Return True if the input is Collection, False otherwise.
    See the definition of Collection in the module doc string.
    """
    try:
        iter(item)
    except TypeError:
        return False
    return not isString(item)

def isSequence(item):
    """Return True if the input is Sequence, False otherwise.
    See the definition of Sequence in the module doc string.
    """
    try:
        item[0:1]
    except (AttributeError, TypeError):
        return False
    return not isString(item)

def isString(item):
    """Return True if the input is a string-like sequence.
    Strings include str, unicode and UserString objects.
    
    From Python Cookbook, 2nd ed.
    """
    return isinstance(item, (basestring, UserString.UserString))

def oneOrNAsList (
    oneOrNVal,
    n,
    valDescr = None,
):
    """Converts a variable that may be a single item
    or a non-string sequence of n items to a list of n items,
    returning a copy.

    Raises ValueError if the input is a sequence of the wrong length.
    
    Inputs:
    - oneOrNVal one value or sequence of values
    - n desired number of values
    - valDescr  string briefly describing the values
        (used to report length error)
    """
    if isSequence(oneOrNVal):
        if len(oneOrNVal) != n:
            valDescr = valDescr or "oneOrNVal"
            raise ValueError("%s has length %d but should be length %d" % (valDescr, len(oneOrNVal), n))
        return list(oneOrNVal)
    else:
        return [oneOrNVal]*n

def removeDups(aSeq):
    """Remove duplicate entries from a sequence,
    returning the results as a list.
    Preserves the ordering of retained elements.
    """
    tempDict = {}
    def isUnique(val):
        if val in tempDict:
            return False
        tempDict[val] = None
        return True
    
    return [val  for val in aSeq if isUnique(val)]

def matchSequences(a, b, rtol=1.0e-5, atol=RO.SysConst.FAccuracy):
    """Compares sequences a and b element by element,
    returning a list of indices for non-matching value pairs.
    The test for matching is compareFloats
    
    This is essentially the same as numpy.allclose,
    but returns a bit more information.
    """
    return [ind for ind in range(len(a))
        if RO.MathUtil.compareFloats(a[ind], b[ind], rtol, atol) != 0]


if __name__ == '__main__':
    class NewStyleClass(object):
        pass
    nsc = NewStyleClass()
    class OldStyleClass:
        pass
    osc = OldStyleClass()
    
    dataDict = {
        isSequence: (
            (nsc, False),
            (osc, False),
            (False, False),
            (5, False),
            (7.5, False),
            (u'unicode string', False),
            ('regular string', False),
            (UserString.UserString("user string"), False),
            (dict(), False),
            (set(), False),
            (list(), True),
            ((), True),
        ),
        isCollection: (
            (nsc, False),
            (osc, False),
            (False, False),
            (5, False),
            (7.5, False),
            (u'unicode string', False),
            ('regular string', False),
            (UserString.UserString("user string"), False),
            (dict(), True),
            (set(), True),
            (list(), True),
            ((), True),
        ),
        isString: (
            (nsc, False),
            (osc, False),
            (False, False),
            (5, False),
            (7.5, False),
            (u'unicode string', True),
            ('regular string', True),
            (UserString.UserString("user string"), True),
            (dict(), False),
            (set(), False),
            (list(), False),
            ((), False),
        ),
    }
    for func, dataList in dataDict.iteritems():
        funcName = func.__name__
        print "testing", funcName
        for dataItem, expectTrue in dataList:
            try:
                assert func(dataItem) == expectTrue
            except AssertionError:
                print "%s(%r) failed; should be %r" % (funcName, dataItem, expectTrue)

    print "testing flatten"
    f = (((),("abc",)), u"abc", ["a", "b", "c"])
    assert flatten(f) == ["abc", u"abc", "a", "b", "c"]
