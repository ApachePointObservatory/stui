#!/usr/bin/env python
"""A dictionary that stores a list of values for each key.

Note: one could subclass dict but this requires writing
explicit methods for setdefault, copy, and possibly others.
Only do this if extra performance is required.

Warning: I intend to rewrite SetDict to use the new set class
in Python 2.3 at some point. Don't use SetDict unless you are
prepared to upgrade to Python 2.3.

History
1-1 Russell Owen 8/8/00
1-2 corrected an indentation error
2003-05-06 ROwen    Test copy and setdefault; renamed to ListDict
                    and added SetDict.
"""
import UserDict

class ListDict(UserDict.UserDict):
    """A dictionary whose values are a list of items.
    """
    def __setitem__(self, key, val):
        """Adds a value to the list of values for a given key,
        creating a new entry if necessary.
        Supports the notation: aListDict[key] = val
        """
        if self.data.has_key(key):
            self.data[key].append(val)
        else:
            self.data[key] = [val]
    
    def addList(self, key, valList):
        """Appends a list of values to the list of values for a given key,
        creating a new entry if necessary.
        """
        valList = list(valList)
        if self.data.has_key(key):
            self.data[key] += valList
        else:
            self.data[key] = valList

    def remove(self, key, val):
        """removes the specified value from the list of values for the specified key;
        raises KeyError if key not found,
        raises ValueError if val not found"""
        self.data.get(key).remove(val)

class SetDict(ListDict):
    """A dictionary whose values are a set of items, meaning
    a list of unique items. Duplicate items are silently not added.
    """
    
    def __setitem__(self, key, val):
        """Adds a value to the set of values for a given key,
        creating a new entry if necessary.
        Supports the notation: aListDict[key] = val
        """
        valSet = self.data.get(key)
        if valSet == None:
            self.data[key] = [val]
        elif val not in valSet:
            valSet.append(val)
    
    def addList(self, key, valList):
        """Appends a list of values to the set of values for a given key,
        creating a new entry if necessary. Duplicate values are elided.
        """
        for val in valList:
            self[key] = val

if __name__ == "__main__":
    import RO.StringUtil

    ad = ListDict()
    ad["a"] = "foo a"
    ad["a"] = "foo a"
    ad["a"] = "bar a"
    ad[1] = "foo 1"
    ad[1] = "foo 2"
    ad[1] = "foo 2"
    ad2 = ad.copy()
    ad2.setdefault("a", "foo")
    ad2.setdefault("a", "foo")
    ad2.setdefault("b", "bar")
    ad2.setdefault("b", "bar")
    print "listdict:"
    print RO.StringUtil.prettyDict(ad)
    print "listdict copy (modified):"
    print RO.StringUtil.prettyDict(ad2)
    

    ad = SetDict()
    ad["a"] = "foo a"
    ad["a"] = "foo a"
    ad["a"] = "bar a"
    ad[1] = "foo 1"
    ad[1] = "foo 2"
    ad[1] = "foo 2"
    ad2 = ad.copy()
    ad2.setdefault("a", "foo")
    ad2.setdefault("a", "foo")
    ad2.setdefault("b", "bar")
    ad2.setdefault("b", "bar")
    print "setdict:"
    print RO.StringUtil.prettyDict(ad)
    print "setdict copy (modified):"
    print RO.StringUtil.prettyDict(ad2)
