#!/usr/bin/env python
"""
History:
2004-05-18 ROwen    Modified test code to use astr instead of str
                    and adict instead of dict.
"""
import re

ptn = re.compile(r'\s*(?P<key>[a-zA-Z_][a-zA-Z0-9_]*)(?:\s*$|(?:\s*(?P<next>[=;])))')

def getKeyword(astr, begInd=0):
    """
    Returns the next keyword from an APO format message. Keywords must start
    with a letter or underscore and may contain those characters or digits thereafter.
    
    Inputs:
        astr: the string to parse
        begInd: the starting index; must point to the beginning of the keyword
            to be extracted, though leading white space is ignored.
    
    Returns a duple containing:
        the next keyword
        the index to the next token (should be "=" or ";"), or None of end-of-string
    
    Exceptions:
        if the next non-whitespace thing is not a keyword, throws a SyntaxError
    """
    mo = ptn.match(astr, begInd)
    if mo == None:
        raise SyntaxError, "not a keyword starting at %d in :%s:" % \
            (begInd,astr)

    keyword = mo.group('key')
    (nextInd, junk) = mo.span('next')
    if nextInd < 0:
        nextInd = None
    return (keyword, nextInd)

if __name__ == '__main__':
    # perform test
    print "testing getKeyword\n"
    testList = [
        ("text = 'test'", 0),
        ("text2 = 'test'", 0),
        ("skipme, text = 'test'", 8),
        ("text='test'", 0),
        ("text ;", 0),
        ("text;", 0),
        ("text=;", 0),
        ("text = ;", 0),
        ("text=", 0),
        ("text = ", 0),
        ("text", 0),
        ("_leadingUnderscore = 'test'", 0),
        ("   _leadingWhitespace = 'test'", 0),
        ("text x 'bad character after keyword'", 0),
        ("text , 'bad character after keyword'", 0),
        ("text, 'bad character immediately after keyword'", 0),
        ("0badKeyStart = 'test'", 0),
        (", badFirstChar = 'test'", 0),
        ("; badFirstChar = 'test'", 0),
        ("'badKeyStart' = 'starts with single quote'", 0),
    ]
    for (astr, nextInd) in testList:
        try:
            (adict, nextInd) = getKeyword(astr, nextInd)
            print "getKeyword('%s') = \"%s\";" % (astr, adict),
            if nextInd != None:
                print "astr[%d] = \"%s\"" % (nextInd, astr[nextInd])
            else:
                print "end of text"
        except StandardError, e:
            print "failed with error: %s" % (e)
