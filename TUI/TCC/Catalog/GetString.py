#!/usr/local/bin/python

def getString(astr, begInd=0):
	"""
Extracts a delimited string value.
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
	the index of the next non-whitespace character, or None if end-of-string

Exceptions:
	if the initial character is not an allowed string delimiter (single
		or double quote) raises a SyntaxError
	if begInd > len(astr) raises an IndexError

History:
2003-06-25 ROwen	From RO.ParseMsg.GetString
2004-05-18 ROwen	Removed unused local variable quoteInd.
					Fixed test code to now use 'str' as a variable.
"""
	quoteChar = astr[begInd]
	if quoteChar not in '\'\"':
		raise SyntaxError, "invalid string delimiter :%s: starting at index %d in data :%s:" % \
			(quoteChar, begInd, astr)
		return None
	if len(astr) <= begInd:
		raise IndexError, "begInd=%d out of range of data :%s:" % (begInd, astr)

	endInd = None
	nextInd = None
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
				foundBslash = False
				stripBslashQuote = True
			else:
				# end of string
				endInd = ind
				break
		else:
			# some character in the string
			foundBslash = False

	if endInd == None:
		raise ValueError, "no closing %r found in %r" % (quoteChar, astr,)

	retStr = astr[begInd+1:endInd]
	if stripBslashBslash:
#		print "stripping double backslash from %r" % retStr
		retStr = retStr.replace("\\\\", "\\")
	if stripBslashQuote:
#		print "stripping backslash %s from %r" % (quoteChar, retStr) 
		retStr = retStr.replace("\\" + quoteChar, quoteChar)

	for ind in range(endInd + 1, len(astr)):
		if astr[ind] not in (" ", "\t"):
			break
	nextInd = ind
			
	return (retStr, nextInd)


if __name__ == '__main__':
	# perform test
	goodList = [
		r'"double quoted string"',
		r"'single quoted string'",
		r'"double quoted string followed by ;"; newkey',
		r'"double quoted string followed by space and ;" 	 ; newkey',
		r'"double quoted string followed by ,", 2',
		r'"embedded \\ pair of backslashes" ;',
		r'"end with pair of backslashes \\" ;',
		r'"double quoted, embedded "" pair of double quotes" ;',
		r'"double quoted, contains pairs: '' and """ ;',
		r'"double quoted, end with pair of double quotes""" ;',
		r"'single quoted, end with pair of single quotes''' ;",
		r'"trailing space " ;',
		r'"backslash-escaped double quote \""',
	]
	badList = [
		r'"missing final \"',
		r'"missing final \";',
	]
	for astr in goodList:
		try:
			(data, ind) = getString(astr)
		except Exception, e:
			print "error: getString(%s) failed with: %s" % (astr, e)
		else:
			if ind == None:
				print "getString(%s) = %s, end of string" % (astr, getString(astr))
			else:
				print "getString(%s) = %s, astr[%d] = %s" % (astr, getString(astr), ind, astr[ind])
	for astr in badList:
		try:
			(data, ind) = getString(astr)
		except Exception, e:
			print "getString correctly rejected %r with %s: %s" % (astr, e.__class__, e)
		else:
			print "error: getString(%s) should have failed but returned %r" % (astr, (data, ind))
