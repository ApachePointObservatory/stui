#!/usr/bin/env python
import sys

def getString(astr, begInd=0):
    """
Extracts a delimited string value from an APO format message.
Strings are delimited with a pair of single or double quotes.
Embedded singles of whichever delimiter is NOT used are ignored,
as are the following character pairs: \" \' "" ''

Inputs:
    astr: the string to parse
    begInd: the starting index; must point to a single or double quote
        that is the beginning of the string value. Leading white space
        is NOT ignored.
Returns a duple consisting of:
    a single string, excluding delimiters
    the index of the next comma or semicolon, or None if end-of-string

Exceptions:
    if the initial character is not an allowed string delimiter (single
        or double quote) raises a SyntaxError
    if begInd > len(astr) raises an IndexError

Warnings printed to sys.stederr:
    if the final string delimiter is found but is not followed
        by , or ; or end of string, then that delimiter is ignored
        and considered to be part of the string; the assumption is
        that the string may contain a another string whose quotes
        were not appropriate "escaped" using the approved character pairs
    if the final string delimiter is missing, complains and returns
        astr[begInd+1:] (all data excluding the initial string delimiter)

History:
2003-03-20 ROwen    Added translation of \\->\, \<q> -> <q>
                    where <q> is the quote character for this particular string
2004-05-18 ROwen    Modified test code to use astr instead of str.
"""

    quoteChar = astr[begInd]
    if quoteChar not in '\'\"':
        raise SyntaxError, "invalid string delimiter :%s: starting at index %d in data :%s:" % \
            (quoteChar, begInd, astr)
        return None
    if len(astr) <= begInd + 1:
        if len(astr) <= begInd:
            raise IndexError, "begInd=%d out of range of data :%s:" % (begInd, astr)
        else:
            sys.stderr.write("string starts at end of data :%s:\n" % (astr))
            return ("", None)

    nextInd = None
    quoteInd = 0
    foundBslash = False
    stripBslashBslash = False
    stripBslashQuote = False
    for ind in range(begInd+1,len(astr)):
        achar = astr[ind]
        if achar == '\\':
            # backslash escapes self, or first backslash
            if foundBslash:
                stripBslashBslash = True
            foundBslash = not foundBslash
        elif achar == quoteChar:
            if foundBslash:
                # backslash escapes quote
                quoteInd = 0
                foundBslash = False
                stripBslashQuote = True
            elif quoteInd == 0:
                quoteInd = ind
            else:
                # quote escapes self
                quoteInd = 0
        elif achar in ',;':
            if quoteInd > 0:
                # found end of string, another value or keyword awaits
                nextInd = ind
                break
            else:
                # character in string; carry on
                foundBslash = False
        elif achar in ' \t':
            # ignore whitespace
            foundBslash = False
        else:
            # some character in the string
            if quoteInd > 0:
                sys.stderr.write ("ignoring extra %s at index %d in data :%s:\n" % \
                    (quoteChar, ind, astr))
                quoteInd = 0
            foundBslash = False

    # no token (comma or semicolon) found; quoteInd = position of closing quote,
    # or zero if missing
    if quoteInd == 0:
        sys.stderr.write ("ignoring missing final %s for string starting at %d in data :%s:\n" % \
            (quoteChar, begInd, astr))
        quoteInd = len(astr)
        nextInd = None
    retStr = astr[begInd+1:quoteInd]
    if stripBslashBslash:
#       print "stripping double backslash from %r" % retStr
        retStr = retStr.replace("\\\\", "\\")
    if stripBslashQuote:
#       print "stripping backslash %s from %r" % (quoteChar, retStr) 
        retStr = retStr.replace("\\" + quoteChar, quoteChar)
    return (retStr, nextInd)


if __name__ == '__main__':
    # perform test
    testList = [
        r'"double quoted string"',
        r"'single quoted string'",
        r'"double quoted string followed by ;"; newkey',
        r'"double quoted string followed by ,", 2',
        r'"embedded \\ pair of backslashes" ;',
        r'"end with pair of backslashes \\" ;',
        r'"double quoted, embedded "" pair of double quotes" ;',
        r'"double quoted, contains pairs: '' and """ ;',
        r'"double quoted, end with pair of double quotes""" ;',
        r"'single quoted, end with pair of single quotes''' ;",
        r'"trailing space " ;',
        r'"backslash-escaped double quote \""',
        r'"missing final \"',
        r'"missing final \";']
    for astr in testList:
        (data, ind) = getString(astr)
        if ind == None:
            print "getString(%s) = %s, end of string" % (astr, getString(astr))
        else:
            print "getString(%s) = %s, astr[%d] = %s" % (astr, getString(astr), ind, astr[ind])
