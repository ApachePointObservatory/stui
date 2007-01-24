#!/usr/bin/env python
"""Obtains all values (0 or more) associated with a keyword.

History:
2002-02-04 ROwen    Allowed additional characters in undelimited strings.
                    Now all ascii printable characters are allowed except ,;='"`\
                    the first 5 are crucial; the others are excluded
                    to enhance readability and reduce possible confusion.
2003-11-19 ROwen    PR 10 fix: could return nextInd=-1 (for 'key=');
                    this could cause the caller to go into an infinite loop.
                    Modified to permit keys with = but no values.
2004-09-14 ROwen    Renamed variable str in test code.
"""
import re
import GetString

_StartRE = re.compile(r"\s*(?P<first>[=;])\s*(?:(?P<next>\S)|$)")

_UndelimWordRE = re.compile(r"(?P<str>[a-zA-Z0-9.\-_+~!@#$%^&*()[\]{}|<>:?/]+?)\s*(?:(?P<next>[,;])|$)")

def getValues(astr, begInd=0):
    """
Extracts all values (zero or more) for a keyword.

Inputs:
    astr: the string to parse
    begInd: index of start, must point to "=" if the keyword has any values
        or ";" if the keyword has no values. Initial whitespace is skipped.

Returns a duple consisting of:
    a tuple of values (empty if there are no values)
    the index of the beginning of the next keyword, or None if end of string

Exceptions:
    If astr[begInd] is not "=" or ";" then raises a SyntaxError
"""
    if begInd == None:
        return ((), None)

    mo = _StartRE.match(astr, begInd)
    if mo == None:
        raise SyntaxError, "cannot find value(s) starting at %d in :%s:" % \
            (begInd, astr)
    sepChar = mo.group('first')
    nextInd = mo.start('next')
    if nextInd < 0:
        # no values and line finished
        return ((), None)
    if sepChar == ';':
        # no values; line not finished
        return ((), nextInd)

    valueList = []

    prevInd = nextInd
#   print "data = :%s:, begInd = %d" % (astr, begInd)
    while True:
#       print "scanning :%s:, i.e. nextInd = %d" % (astr[nextInd:], nextInd)
        nextIsKey = False
        if astr[nextInd] in "\'\"":
            # value is a delimited string
#           print "looking for a delimited string"
            (value, nextInd) = GetString.getString(astr, nextInd)
            valueList.append(value)

        elif astr[nextInd] != ';':
            # value is an undelimited word (e.g. a number, NaN, etc.)
#           print "looking for an undelimited word starting at %d" % (nextInd)
            mo = _UndelimWordRE.match(astr, nextInd)
            if mo == None:
                raise SyntaxError, "cannot find an undelimited word starting at %d in :%s:" % \
                    (nextInd, astr)
            value = mo.group('str')
            nextInd = mo.start('next')
            if (nextInd < 0):
                nextInd = None

            valueList.append(value)

#       print "valueList =", valueList, "nextInd =", nextInd,
#       if nextInd != None:
#           print "char at nextInd =", astr[nextInd]
#       else:
#           print ""
        
        if nextInd == None:
            # done with line
            break

        # nextInd points to comma or semicolon
        if astr[nextInd] == ';':
            nextIsKey = True
        elif astr[nextInd] != ',':
            print "bug; expected comma or semicolon as next token; giving up on line"
            nextInd = None
            break

        if (nextInd <= prevInd) and not nextIsKey:
            print "bug: nextInd = %d <= prevInd = %d" % (nextInd, prevInd)
            nextInd = None
            break

        # find index of next character
        for ind in range(nextInd+1, len(astr)):
            if astr[ind] not in ' \t':
                nextInd = ind
                break
        else:
            print "ignoring separator \"%s\" at end of data :%s:" % \
                (astr[nextInd], astr)
            nextInd = None
            break

        if nextInd >= len(astr):
            break

        if nextIsKey:
            break


        prevInd = nextInd

    return (tuple(valueList), nextInd)


if __name__ == '__main__':
    # perform test
    testList = [
        '= 1, 2, 3',
        '=1,2,3',
        r'''="str1", 'str2', "str3 with dble dble-quote ""escape"""''',
        '=UndelimStr, Again, Another',
        '=NaN, nan, naN, Nan, 5, 6, "str7"',
        '= 1, 2, 3; key2; text="extra keywords"',
        '; text="no values"',
        ' ? text="bad start char"',
        ' x text="bad start char"',
        '= , 2, 3; text="missing value in list"',
        '= 1, 2, ; text="missing value in list"',
        '= 1, 2, "end with separator",',
        '=3.14159, "next value"; nextKey',
        ' = 3.14159, 1, "next value"; nextKey',
        ' = 2003-02-04T12:56:19.788Z, 1, "next value"; nextKey',
        '=',
        '= ;',
    ]

    for testStr in testList:
        try:
            (data, nextInd) = getValues(testStr)
            print "getValues('%s') = %s;" % (testStr, `(data, nextInd)`),
            if nextInd != None:
                print "str[%d] = \"%s\"" % (nextInd, testStr[nextInd])
            else:
                print "end of string"
        except StandardError, e:
            print "failed with error: %s" % (e)
