#!/usr/local/bin/python
"""Parses the header from a keyword/variable string in various formats

History:
2002-12-13 ROwen    Bug fix in getHubHeader: dataStart was wrong (fix by Craig Loomis).
                    Mod. getHubHeader and getMidRidHeader to use re.start instead of re.span.
2002-12-16 ROwen    Mod. to return dataStart = len(astr) if no data (instead of None);
                    renamed getStdHeader to getHubHeader and getMidRidAsStdHeader to getMidRidAsHubHeader.
2003-06-18 ROwen    Modified to test for StandardError instead of Exception
2003-10-01 ROwen    Allow cmdr to have a leading period.
2004-05-18 ROwen    Stopped importing string; it wasn't used.
                    Modified test code to use astr instead of str.
"""
import re

_HubPattern = re.compile(r'^\s*(?P<cmdr>[_.a-zA-Z][-_.a-zA-Z0-9]*)\s+(?P<cmdID>-?\d+)\s+(?P<actor>[_a-zA-Z][-_.a-zA-Z0-9]*)\s+(?P<type>\S)(?:\s*$|(?:\s+(\S)))')
_MidRidPattern = re.compile(r'^\s*(?P<mid>-?\d+)\s+(?P<rid>-?\d+)\s+(?P<type>\S)(?:\s*$|(?:\s+(\S)))')

def getHubHeader(astr):
    """Extracts the commander, cmdID and actor from a string in the format:
        cmdr cmdID actor type msg

    Inputs:
    - astr: the string to parse

    Returns a duple:
    - headerDict: a dictionary containing:
      - "cmdr": commander (string)
      - "cmdID": command ID number (integer)
      - "actor": actor (string)
      - "type": type of message (character)
    - dataStart: the index of the first non-whitespace character following the header,
        or len(astr) if no data follows the header
    
    Exceptions:
    - If the header cannot be fully parsed, throws a SyntaxError.
    """
    matchObj = _HubPattern.match(astr)
    if matchObj == None:
        raise SyntaxError, "could not parse standard header in :%s:" % (astr)

    dataStart = matchObj.start(5)
    if dataStart < 0:
        dataStart = len(astr)
    headerDict = matchObj.groupdict()

    # convert cmdID to an integer
    try:
        headerDict['cmdID'] = int(headerDict['cmdID'])
    except StandardError:
        raise SyntaxError, "bug! could not convert cmdID %r to integer in :%s:" % (headerDict['cmdID'], astr)
    return (headerDict, dataStart)


def getMidRidHeader(astr):
    """Extracts the commander, cmdID and actor from a string in the format: mid rid type msg

    Inputs:
    - astr: the string to parse
    
    Returns a duple:
    - headerDict: a dictionary containing:
      - "mid": message ID (integer)
      - "rid": reply ID (integer)
      - "type": type of message (character)
    - dataStart: the index of the first non-whitespace character following the header,
        or len(astr) if no data follows the header
    
    Exceptions:
    - If the header cannot be fully parsed, throws a SyntaxError.
    """
    matchObj = _MidRidPattern.match(astr)
    if matchObj == None:
        raise SyntaxError, "could not parse mid/rid header in :%s:" % (astr)

    dataStart = matchObj.start(4)
    if dataStart < 0:
        dataStart = len(astr)
    headerDict = matchObj.groupdict()

    # convert mid and rid to integers
    try:
        headerDict['mid'] = int(headerDict['mid'])
        headerDict['rid'] = int(headerDict['rid'])
    except StandardError:
        raise SyntaxError, "bug! could not convert mid or rid to integer in :%s:" % (astr)
    return (headerDict, dataStart)


def getMidRidAsHubHeader(astr, cmdr="", actor=""):
    """Extracts data from a mid, rid header and returns it as a standard header.

    Inputs:
    - astr: the string to parse
    - cmdr: the desired commander
    - actor: the desired actor
    
    Returns a duple:
    - headerDict: a dictionary containing:
      - "cmdr": commander (string)
      - "cmdID": command ID number (integer)
      - "actor": actor (string)
      - "type": type of message (character)
    - dataStart: the index of the first non-whitespace character following the header,
        or len(astr) if no data follows the header
    
    Exceptions:
    - If the header cannot be fully parsed, throws a SyntaxError.
    """
    headerDict, dataStart = getMidRidHeader(astr)
    headerDict.update({
        "actor":actor,
        "cmdr":cmdr,
        "cmdID":headerDict["mid"],
    })
    del(headerDict["mid"])
    del(headerDict["rid"])
    return (headerDict, dataStart)


if __name__ == '__main__':
    # perform tests
    print "testing getHubHeader\n"
    testList = [
        "me  456 TCC > keyword",
        "me.hub -90 spicam i",
        "me 2 TCC badType_NotOneChar",
        "me TCC missingCIDAndType",
    ]
    for astr in testList:
        try:
            (headerDict, dataStart) = getHubHeader(astr)
            print "GetHeader('%s') = %s;" % (astr, headerDict),
            print "astr[%d:] = %r" % (dataStart, astr[dataStart:])
        except StandardError, e:
            print "failed with error: %s" % (e)
    
    print "testing getMidRidHeader\n"
    testList = [
        "123  456 > keyword",
        "-78  -90 i",
        "1 2 badType_NotOneChar",
        "1 missingRID",
    ]
    for astr in testList:
        try:
            (headerDict,dataStart) = getMidRidHeader(astr)
            print "GetHeader('%s') = %s;" % (astr, headerDict),
            print "astr[%d:] = %r" % (dataStart, astr[dataStart:])
        except StandardError, e:
            print "failed with error: %s" % (e)


    print "testing getMidRidAsHubHeader\n"
    testList = [
        "123  456 > keyword",
        "-78  -90 i",
        "1 2 badType_NotOneChar",
        "1 missingRID",
    ]
    for astr in testList:
        try:
            (headerDict, dataStart) = getMidRidAsHubHeader(astr, cmdr="me", actor="tcc")
            print "GetHeader('%s') = %s;" % (astr, headerDict),
            print "astr[%d:] = %r" % (dataStart, astr[dataStart:])
        except StandardError, e:
            print "failed with error: %s" % (e)
