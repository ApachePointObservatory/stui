#!/usr/bin/env python
"""Parse a keyword-value message.

History:
2002-12-16 ROwen
2003-06-25 ROwen    Modified to return an RO.Alg.OrderedDict
2003-11-19 ROwen    Modified header: keywords with no values may have an '='.
                    Added "noValKey=" to test cases as it caused an infinite loop.
2004-05-18 ROwen    Modified test code to use astr instead of str.
"""
from GetKeyword import getKeyword
from GetValues import getValues
import RO.Alg

def parseKeyValueData(astr):
    """Parses a string of the form:
        'keyword1=value11, value12,...; keyword2=value21, value22; keyword3=; keyword4; ...'
    returning an RO.Alg.OrderedDict of the form:
        {keyword1:(value11, value12,...), keyword2:(value21, value22, ...),
         keyword3: (), keyword4: (), ...}
        
    Inputs:
    - astr: the string to parse, of the form:
        keyword1=value11, value12,...; keyword2=value21, value22...
    where:
    - keyword is a keyword; it must start with a letter or underscore
        and may contain those characters or digits thereafter.
    - value is the value of the keyword, one of:
        an integer
        a floating point number
        a string delimited by a pair of single or double quotes
            any enclosed characters identical to the delimiter
            should be escaped by doubling or preceding with a backslash
    - Each keyword may have zero or more comma-separated values;
        if it has zero values then the equals sign may be omitted.
    
    Returns dataDict, an RO.Alg.OrderedDict of keyword: valueTuple entries,
    one for each keyword. Details:
    - The keywords are given in the order they were specified in the message.
    - If the keyword has no values, valueTuple is ()
    - If the keyword has one value, valueTuple is (value,)
    """
    dataDict = RO.Alg.OrderedDict()
    if astr == '':
        return dataDict
    nextInd = 0
    while nextInd != None:
        keyword, nextInd = getKeyword(astr, nextInd)
        # print "got keyword %r; nextInd = %r" % (keyword, nextInd)
        valueTuple, nextInd = getValues(astr, nextInd)
        # print "got valueTuple %r; nextInd = %r" % (valueTuple, nextInd)
        dataDict[keyword] = valueTuple
    return dataDict

if __name__ == '__main__':
    # perform test
    print "testing parseHubMsg\n"
    testList = [
        "keyword",
        "",
        "strSet='quoted \"string\" 1', 'quoted \"string\" 2', unquotedstr3",
        "genSet=1, 2, 3.14159, 'str4', 'str5'",
        "noValKey1=",
        "noValKey1; intKey2=2; noValKey3=; noValKey4 = ; noValKey5",
    ]
    for astr in testList:
        try:
            dataDict = parseKeyValueData(astr)
            print "parseHubMsg(%r) = {" % (astr,)
            for key, value in dataDict.iteritems():
                print "    %r: %r" % (key, value)
            print "}"
        except StandardError, e:
            print "failed with error: ", e
