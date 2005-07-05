#!/usr/local/bin/python
"""String utilities, with an emphasis on support for sexagesimal numbers
(e.g. degrees:minutes:seconds).

To do:
- add tests for quoteStr,...?
- 

History:
2001-03-12 ROwen	strToFloat modified to handle ".".
2001-03-14 ROwen	Added prettyDict; still need to add a test for it.
2001-04-13 ROwen	Fixed a bug in splitDMSStr: -0:... was not retaining the minus sign;
	added dmsStrToSec, which may be useful for handling durations;
	modified splitDMSStr to allow an arbitrary number digits in the first field
	(use range checking of the equivalent numeric value to limit this),
	to return sing as a separate entity, and to return all strings;
	improved the test suite, including adding a nearly silent test.
2001-04-20 ROwen	Fixed a bug in degToDMSStr: borderline cases could print
	as 60 instead of 00 and incrementing the next field.
2001-07-22 ROwen	Made DegStr work on unix as well as Mac
    (I still don't know the Windows character).
2001-08-29 ROwen	Made DegStr and DMSStr unicode strings, a reasonable choice
    now that one can print unicode characters.
2001-11-01 ROwen	Added nFields argument to degToDMSStr and secToDMSStr;
	changed degToDMSStr, secToDMSStr and neatenDMSStr to eliminate leading spaces.
2002-08-08 ROwen	Moved to RO and renamed from ROStringUtil. Renamed
	 xToY functions to yFromX. Hid private constants with leading underscore.
2002-08-21 ROwen	Modified splitDMSStr to require all but the first field be <60.
2003-04-04 ROwen	Bug fix: dmsStrFromDeg and dmsStrFromSec mis-handled
	some negative values.
2003-06-19 ROwen	Fixed two tests which broke in upgrades listed above.
2003-07-15 ROwen	Added omitExtraFields to degFromDMSStr and secFromDMSStr;
					added quoteStr function.
2003-10-27 ROwen	Added plural function.
2004-01-09 ROwen	Added AngstromStr, LambdaStr and MuStr constants.
2004-05-18 ROwen	Stopped importing sys since it was not being used.
2005-06-27 ROwen	Fixed a nonfunctional assert statement in splitDMSStr.
"""
import re

AngstromStr = u"\N{ANGSTROM SIGN}"
DegStr = u"\N{DEGREE SIGN}"
DMSStr = DegStr + u"'\""
LambdaStr = u"\u00c5" # for some reason this fails: u"\N{GREEK SMALL LETTER LAMBDA}"
MuStr = u"\N{GREEK SMALL LETTER MU}"

def dmsStrFromDeg (decDeg, nFields=3, precision=1, omitExtraFields = False):
	"""Converts a number to a sexagesimal string with 1-3 fields.

	Inputs:
		decDeg: value in decimal degrees or hours
		nFields: number of fields; <=1 for dddd.ddd, 2 for dddd:mm.mmm, >=3 for dddd:mm:ss.sss
		precision: number of digits after the decimal point in the last field
	"""
	# first convert the number of seconds and round to the appropriate # of digits
	if precision > 0:
		minFloatWidth = precision + 3
	else:
		minFloatWidth = 2
	
	if decDeg < 0:
		signStr = "-"
		decDeg = abs(decDeg)
	else:
		signStr = ""
	
	if nFields <= 1  or (omitExtraFields and numSec == 0 and numMin == 0):
#		if nFields < 1 and decDeg == 0.0:
#			return ""
		return "%s%.*f" % (signStr, precision, decDeg)
	elif nFields == 2  or (omitExtraFields and numSec == 0):
		decDeg = float ("%.*f" % (precision, decDeg * 60.0)) / 60.0
		# now extract degrees, minutes and seconds fields
		(numDeg, frac) = divmod (abs(decDeg), 1.0)
		numMin = frac * 60.0
		return "%s%.0f:%0*.*f" % (signStr, numDeg, minFloatWidth, precision, numMin)
	else:
		# round decDeg to prevent roundup problems in the seconds field later
		decDeg = float ("%.*f" % (precision, decDeg * 3600.0)) / 3600.0
		if decDeg == -0.0:
			decDeg = 0.0  # works around a bug with -0.0: abs(-0.0) = -0.0
		# now extract degrees, minutes and seconds fields
		(numDeg, frac) = divmod (abs(decDeg), 1.0)
		(numMin, frac) = divmod (frac * 60.0, 1.0)
		numSec = frac * 60.0
		return "%s%.0f:%02.0f:%0*.*f" % (signStr, numDeg, numMin, minFloatWidth, precision, numSec)

def dmsStrFromSec (decSec, nFields=3, precision=1, omitExtraFields = True):
	"""Converts a number, in seconds, to a sexagesimal string.
	Unlike dmsStrFromDeg, nFields is counted right to left.

	Inputs:
		decSec: value in decimal seconds or arc seconds
		nFields: number of fields; <=1 for ss.sss, 2 for mm:ss.ss, >=3 for dddd:mm:ss.sss
		precision: number of digits after the decimal point in the seconds field
		omitExtraFields: omit fields that are zero, starting from the left.
	"""
	decDeg = decSec / 3600.0
	if decDeg < 0:
		signStr = "-"
		decDeg = abs(decDeg)
	else:
		signStr = ""

	# round decDeg to prevent roundup problems in the seconds field later
	decDeg = float ("%.*f" % (precision, decDeg * 3600.0)) / 3600.0
	# now extract degrees, minutes and seconds fields
	(numDeg, frac) = divmod (abs(decDeg), 1.0)
	(numMin, frac) = divmod (frac * 60.0, 1.0)
	numSec = frac * 60.0

	if precision > 0:
		minFloatWidth = precision + 3
	else:
		minFloatWidth = 2
	
	if nFields <= 1 or (omitExtraFields and numDeg == 0 and numMin == 0):
#		if nFields < 1 and decDeg == 0.0:
#			return ""
		return "%s%.*f" % (signStr, precision, (((numDeg * 60) + numMin) * 60) + numSec)
	elif nFields == 2 or (omitExtraFields and numDeg == 0):
		return "%s%.0f:%0*.*f" % (signStr, (numDeg * 60) + numMin, minFloatWidth, precision, numSec)
	else:
		return "%s%.0f:%02.0f:%0*.*f" % (signStr, numDeg, numMin, minFloatWidth, precision, numSec)

def degFromDMSStr (dmsStr):
	"""Converts a string of the basic form dd[:mm[:ss]] to decimal degrees.
	See splitDMSStr for details of the format.
	
	error conditions:
		raises ValueError if the string cannot be parsed
	"""
	dmsItems = splitDMSStr(dmsStr)

	# extract sign
	if dmsItems[0] == '-':
		signMult = -1.0
	else:
		signMult = 1.0
	dmsItems[0:1] = []

	# combine last two elements and convert to float
	dmsItems[-2:] = [floatFromStr(dmsItems[-2]) + floatFromStr(dmsItems[-1])]

	# convert all but last item to float
	for ind in range(len(dmsItems) - 1):
		dmsItems[ind] = intFromStr(dmsItems[ind])
	
	dmsItems.reverse()
	decDeg = 0.0
	for dmsField in dmsItems:
		decDeg = abs(dmsField) + (decDeg / 60.0)
	return signMult * decDeg

def secFromDMSStr (dmsStr):
	"""Converts a string of the basic form [[dd:]mm:]ss to decimal degrees.
	Note that missing fields are handled differently than degFromDMSStr!
	See splitDMSStr for details of the format.
	
	error conditions:
		raises ValueError if the string cannot be parsed
	"""
	dmsItems = splitDMSStr(dmsStr)

	# extract sign
	if dmsItems[0] == '-':
		signMult = -1.0
	else:
		signMult = 1.0
	dmsItems[0:1] = []

	# combine last two elements and convert to float
	dmsItems[-2:] = [floatFromStr(dmsItems[-2]) + floatFromStr(dmsItems[-1])]

	# convert all but last item to float
	for ind in range(len(dmsItems) - 1):
		dmsItems[ind] = intFromStr(dmsItems[ind])
	
	decSec = 0.0
	for dmsField in dmsItems:
		decSec = abs(dmsField) + (decSec * 60.0)
	return signMult * decSec

def secStrFromDMSStr(dmsStr):
	"""Converts a string of the basic form [[dd:]mm:]ss to decimal seconds
	preserving the original accuracy of seconds
	Note that missing fields are handled differently than degFromDMSStr!
	See splitDMSStr for details of the format.
	
	error conditions:
		raises ValueError if the string cannot be parsed
	"""
	dmsItems = splitDMSStr(dmsStr)

	# extract sign and fractional seconds (includes decimal point)
	signStr = dmsItems[0]
	fracSecStr = dmsItems[-1]

	# compute integer seconds
	# convert all but first and last items to integers
	intList = [intFromStr(item) for item in dmsItems[1:-1]]
	
	intSec = 0
	for intVal in intList:
		intSec = abs(intVal) + (intSec * 60)
	return "%s%s%s" % (signStr, intSec, fracSecStr)

FloatChars = "0123456789+-.eE"

def checkDMSStr(dmsStr):
	"""Verifies a sexagesimal string; returns 1 if valid, 0 if not
	"""
	try:
		splitDMSStr(dmsStr)
		return 1
	except:
		return 0

def dmsStrFieldsPrec(dmsStr):
	"""Returns the following information about a sexagesimal string:
	- the number of colon-separated fields
	- the precision of the right-most field
	"""
	if dmsStr == "":
		return (0, 0)

	precArry = dmsStr.split(".")
	if len(precArry) > 1:
		precision = len(precArry[1])
	else:
		precision = 0
	nFields = dmsStr.count(":") + 1
	return (nFields, precision)
	
def findLeftNumber(astr, ind):
	"""Finds the starting and ending index of the number
	enclosing or to the left of index "ind".
	Returns (None, None) if no number found.

	Warning: this is not a sophisticated routine. It looks for
	the a run of characters that could be present
	in a floating point number. It does not sanity checking
	to see if they make a valid number.
	"""
	leftInd = _findLeftOfLeftNumber(astr, ind)
	if leftInd == None:
		return (None, None)
	rightInd = _findRightOfRightNumber(astr, leftInd)
	if rightInd == None:
		return (None, None)
	return (leftInd, rightInd)

def findRightNumber(astr, ind):
	"""Finds the starting and ending index of the number
	enclosing or to the right of index "ind".
	Returns (None, None) if no number found.

	Warning: this is not a sophisticated routine. It looks for
	the a run of characters that could be present
	in a floating point number. It does not sanity checking
	to see if they make a valid number.
	"""
	rightInd = _findRightOfRightNumber(astr, ind)
	if rightInd == None:
		return (None, None)
	leftInd = _findLeftOfLeftNumber(astr, rightInd)
	if leftInd == None:
		return (None, None)
	return (leftInd, rightInd)

def _findLeftOfLeftNumber(astr, ind):
	"""Finds the index of the first character of the number
	enclosing or to the left of index "ind".
	Returns None if no number found.

	Warning: this is not a sophisticated routine. It looks for
	the left-most of a run of characters that could be present
	in a floating point number. It does not sanity checking
	to see if they make a valid number.
	"""
	leftInd = None
	for tryind in range(ind, -1, -1):
		if astr[tryind] in FloatChars:
			leftInd = tryind
		elif leftInd != None:
			break
	return leftInd

def _findRightOfRightNumber(astr, ind):
	"""Finds the index of the last character of the number
	enclosing or to the right of index "ind".
	Returns None if no number found.

	Warning: this is not a sophisticated routine. It looks for
	the right-most of a run of characters that could be present
	in a floating point number. It does not sanity checking
	to see if they make a valid number.
	"""
	rightInd = None
	for tryind in range(ind, len(astr)):
		if astr[tryind] in FloatChars:
			rightInd = tryind
		elif rightInd != None:
			break
	return rightInd

def neatenDMSStr (dmsStr):
	"""Converts a sexagesimal string to a neater version.
	
	error conditions:
		raises ValueError if the string cannot be parsed
	"""
	if dmsStr == "":
		return ""

	precArry = dmsStr.split(".")
	if len(precArry) > 1:
		precision = len(precArry[1])
	else:
		precision = 0
	fieldArry = dmsStr.split(":")
	nFields = len(fieldArry)
	
	floatValue = degFromDMSStr(dmsStr)
	return dmsStrFromDeg(floatValue, nFields=nFields, precision=precision)

def plural(num, singStr, plStr):
	"""Returns singStr or plStr depending if num == 1 or not.
	A minor convenience for formatting messages (in lieu of ?: notation)
	"""
	if num == 1:
		return singStr
	return plStr

def prettyDict(aDict, entrySepStr = "\n", keyValSepStr = ": "):
	"""Formats a dictionary in a nice way
	
	Inputs:
	aDict: the dictionary to pretty-print
	entrySepStr: string separating each dictionary entry
	keyValSepStr: string separating key and value for each entry
	
	Returns a string containing the pretty-printed dictionary
	"""
	sortedKeys = aDict.keys()
	sortedKeys.sort()
	eltList = []
	for aKey in sortedKeys:
		eltList.append(str(aKey) + keyValSepStr + str(aDict[aKey]))
	return entrySepStr.join(eltList)

# constants used by splitDMSStr
# DMSRE = re.compile(r"^\s*([+-]?)(\d{0,3})\s*(?:\:\s*(\d{0,2})\s*){0,2}(\.\d*)?\s*$")
_DegRE =       re.compile(r"^\s*([+-]?)(\d*)(\.\d*)?\s*$")
_DegMinRE =    re.compile(r"^\s*([+-]?)(\d*)\s*\:\s*([0-5]?\d?)(\.\d*)?\s*$")
_DegMinSecRE = re.compile(r"^\s*([+-]?)(\d*)\s*\:\s*([0-5]?\d?):\s*([0-5]?\d?)(\.\d*)?\s*$")

def splitDMSStr (dmsStr):
	"""splits a sexagesimal string into fields
	returns one of the following lists:
	[sign, int deg, frac deg]
	[sign, int deg, int min, frac min]
	[sign, int deg, int min, int sec, frac sec]
	where:
		all values are strings
		sign is one of ('', '+' or '-')
		frac <whatever> includes a leading decimal point
	
	error conditions:
		raises ValueError if the string cannot be parsed
	"""
	assert isinstance(dmsStr, str)
	m = _DegRE.match(dmsStr) or _DegMinRE.match(dmsStr) or _DegMinSecRE.match(dmsStr)
	if m == None:
		raise ValueError, "splitDMSStr cannot parse %s as a sexagesimal string" % (dmsStr)
	matchSet = list(m.groups())
	if matchSet[-1] == None:
		matchSet[-1] = ''
	return matchSet

_FloatRE = re.compile(r'^\s*[-+]?[0-9]*\.?[0-9]*(e[-+]?)?[0-9]*\s*$', re.IGNORECASE)
_FloatNoExpRE = re.compile(r'^\s*[-+]?[0-9]*\.?[0-9]*\s*$')
def floatFromStr(astr, allowExp=1):
	"""converts a string representation of a number to a float;
	unlike float(), partial representations (such as "", "-", "-.e") are taken as 0
	and "nan" is forbidden.

	error conditions:
		raises ValueError if astr cannot be converted
	"""
	if allowExp:
		match = _FloatRE.match(astr)
	else:
		match = _FloatNoExpRE.match(astr)
	
	
	if match == None:
		raise ValueError, "cannot convert :%s: to a float" % (astr)
		
	try:
		return float(astr)
	except:
		# partial float
		return 0.0

_IntRE = re.compile(r'^\s*[-+]?[0-9]*\s*$')
def intFromStr(astr):
	"""converts a string representation of a number to an integer;
	unlike int(), the blank string and "+" and "-" are treated as 0

	error conditions:
		raises ValueError if astr cannot be converted
	"""
	if _IntRE.match(astr) == None:
		raise ValueError, "cannot convert :%s: to an integer" % (astr)

	try:
		return int(astr)
	except:
		# partial int
		return 0

def quoteStr(astr, escChar = '\\', quoteChar = '"'):
	"""Escapes all instances of quoteChar and escChar in astr
	with a preceding escChar and surrounds the result with quoteChar.
	
	Examples:
	astr = 'foo" \bar'
	quoteStr(astr) = '"foo\" \\bar"'
	quoteStr(astr, escChar = '"') = '"foo"" \bar"'

	This prepares a string for output.
	"""
	if escChar != quoteChar:
		# escape escChar
		astr = astr.replace(escChar, escChar + escChar)
	# escape quoteChar and surround the result in quoteChar
	return quoteChar + astr.replace(quoteChar, escChar + quoteChar) + quoteChar

def _assertTest():
	"""Runs a test by comparing results to those expected and only failing if something is wrong.
	"""
	testSet = (
		['::', '', 1, ['', '', '', '', ''], 0.0, 0.0, '0:00:00', ['0:00:00', '0:00:00.0', '0:00:00.00']],
		['-::', '', 1, ['-', '', '', '', ''], -0.0, -0.0, '0:00:00', ['0:00:00', '0:00:00.0', '0:00:00.00']],
		['-0:00:00.01', '', 1, ['-', '0', '00', '00', '.01'], -2.77777777778e-06, -0.01, '-0:00:00.01', ['-0:00:00', '-0:00:00.0', '-0:00:00.01']],
		[' +1', '', 1, ['+', '1', ''], 1.0, 1.0, '1', ['1:00:00', '1:00:00.0', '1:00:00.00']],
		['-1.2345', '', 1, ['-', '1', '.2345'], -1.2345, -1.2345, '-1.2345', ['-1:14:04', '-1:14:04.2', '-1:14:04.20']],
		['-123::', '', 1, ['-', '123', '', '', ''], -123.0, -442800.0, '-123:00:00', ['-123:00:00', '-123:00:00.0', '-123:00:00.00']],
		['-123:4', '', 1, ['-', '123', '4', ''], -123.066666666667, -7384.0, '-123:04', ['-123:03:60', '-123:03:60.0', '-123:03:60.00']],
		['-123:45', '', 1, ['-', '123', '45', ''], -123.75, -7425.0, '-123:45', ['-123:45:00', '-123:45:00.0', '-123:45:00.00']],
		['-123:4.56789', '', 1, ['-', '123', '4', '.56789'], -123.0761315, -7384.56789, '-123:04.56789', ['-123:04:34', '-123:04:34.1', '-123:04:34.07']],
		['-123:45.6789', '', 1, ['-', '123', '45', '.6789'], -123.761315, -7425.6789, '-123:45.6789', ['-123:45:41', '-123:45:40.7', '-123:45:40.73']],
		['1:2:', '', 1, ['', '1', '2', '', ''], 1.0333333333, 3720.0, '1:02:00', ['1:02:00', '1:02:00.0', '1:02:00.00']],
		['1:2:3', '', 1, ['', '1', '2', '3', ''], 1.03416666667, 3723.0, '1:02:03', ['1:02:03', '1:02:03.0', '1:02:03.00']],
		['1:2:3.456789', '', 1, ['', '1', '2', '3', '.456789'], 1.0342935525, 3723.456789, '1:02:03.456789', ['1:02:03', '1:02:03.5', '1:02:03.46']],
		['1:23:4', '', 1, ['', '1', '23', '4', ''], 1.3844444444, 4984.0, '1:23:04', ['1:23:04', '1:23:04.0', '1:23:04.00']],
		['1:23:45', '', 1, ['', '1', '23', '45', ''], 1.3958333333, 5025.0, '1:23:45', ['1:23:45', '1:23:45.0', '1:23:45.00']],
		['123:45:6.789', '', 1, ['', '123', '45', '6', '.789'], 123.7518858333, 445506.789, '123:45:06.789', ['123:45:07', '123:45:06.8', '123:45:06.79']],
		['123:45:56.789', '', 1, ['', '123', '45', '56', '.789'], 123.765774722, 445556.789, '123:45:56.789', ['123:45:57', '123:45:56.8', '123:45:56.79']],
		['-0::12.34', 'bug test; the sign must be retained', 1, ['-', '0', '', '12', '.34'], -0.00342777778, -12.34, '-0:00:12.34', ['-0:00:12', '-0:00:12.3', '-0:00:12.34']],
		['-::12.34', 'a weird gray area, but it works', 1, ['-', '', '', '12', '.34'], -0.00342777778, -12.34, '-0:00:12.34', ['-0:00:12', '-0:00:12.3', '-0:00:12.34']],
		['::12.34', '', 1, ['', '', '', '12', '.34'], 0.00342777778, 12.34, '0:00:12.34', ['0:00:12', '0:00:12.3', '0:00:12.34']],
		['1:23.4567', '', 1, ['', '1', '23', '.4567'], 1.390945, 83.4567, '1:23.4567', ['1:23:27', '1:23:27.4', '1:23:27.40']],
		['-1.234567', '', 1, ['-', '1', '.234567'], -1.234567, -1.234567, '-1.234567', ['-1:14:04', '-1:14:04.4', '-1:14:04.44']],
		['-1:abadstr', 'invalid characters', 0, None, None, None, None, None],
		['-1:2343:24', 'too many minutes digits', 0, None, None, None, None, None],
		['1:-1:24', 'minus sign in wrong place', 0, None, None, None, None, None],
	)
	def locAssert(fmt, res, func, *args, **kargs):
		assert fmt % (res,) == fmt % (func(*args, **kargs),), "%r != %r = %s(*%r, **%r)" % (res, func(*args, **kargs), func.__name__, args, kargs)
	
	nErrors = 0
	for testStr, commentStr, isOK, splitStr, degVal, secVal, neatStr, dmsStr02 in testSet:
		try:
			locAssert("%r", splitStr, splitDMSStr, testStr)
			locAssert("%.8g", degVal, degFromDMSStr, testStr)
			locAssert("%.8g", secVal, secFromDMSStr, testStr)
			locAssert("%r", neatStr, neatenDMSStr, testStr)
			locAssert("%r", dmsStr02[0], dmsStrFromDeg, degVal, 3, 0)
			locAssert("%r", dmsStr02[1], dmsStrFromDeg, degVal, 3, 1)
			locAssert("%r", dmsStr02[2], dmsStrFromDeg, degVal, 3, 2)
			if not isOK:
				print "unexpected success on %r" % testStr
				nErrors += 1
		except StandardError, e:
			if isOK:
				print "unexpected failure on %r\n\t%s\nskipping other tests on this value" % (testStr, e)
				nErrors += 1
	if nErrors == 0:
		print "RO.StringUtil passed"
	else:
		print "RO.StringUtil failed with %d errors" % nErrors
			

def _printTest(dmsSet = None):
	"""Prints the results of running each routine on a set of test data.
	Data format is a list of tuples, each containing three elements:
		dmsStr to test, a comment, and isOK (true if the dmsStr is valid, false if not)
		
	The output is in the format used by _assertTest, but please use this with great caution.
	You must examine the output very carefully to confirm it is correct before updating _assertTest!
	"""
	print "Exercising RO string utilities"
	if not dmsSet:
		dmsSet = (
			("::", ""),
			("-::", ""),
			(" +1", ""),
			("-2.999998639", ""),	# 3:00:00 = 3:00:00.0 = 3:00:00.00 = 2:59:59.9951
			("-2.999998583", ""),	# 3:00:00 = 3:00:00.0 = 2:59:59.99 = 2:59:59.9949
			("-2.999986139", ""),	# 3:00:00 = 3:00:00.0 = 2:59:59.95 = 2:59:59.9501
			("-2.999986083", ""),	# 3:00:00 = 2:59:59.9 = 2:59:59.95 = 2:59:59.9499
			("-2.999861139", ""),	# 2:59:59 = 2:59:59.5 = 2:59:59.50 = 2:59:59.5001
			("-2.999861083", ""),	# 2:59:59 = 2:59:59.5 = 2:59:59.50 = 2:59:59.4999
			("-123::", ""),
			("-123:4", ""),
			("-123:45", ""),
			("-123:4.56789", ""),
			("-123:45.6789", ""),
			("1:2:", ""),
			("1:2:3", ""),
			("1:2:3.456789", ""),
			("1:23:4", ""),
			("1:23:45", ""),
			("123:45:6.789", ""),
			("123:45:56.789", ""),
			("-0::12.34", "bug test; the sign must be retained"),
			("-::12.34", "a weird gray area, but it works"),
			("::12.34", ""),
			("1:23.4567", ""),
			("-1.234567", ""),
			("-1:abadstr", "invalid characters"),
			("-1:2343:24", "too many minutes digits"),
			("1:-1:24", "minus sign in wrong place"),
		)
	for testStr, commentStr in dmsSet:
		# note: if splitDMSStr succeeds, then the other calls all should succeed
		if checkDMSStr(testStr):
			try:
				itemList = splitDMSStr(testStr)
				deg = degFromDMSStr (testStr)
				sec = secFromDMSStr (testStr)
				neatStr = neatenDMSStr (testStr)
				outDMSStr = []
				for prec in range(3):
					outDMSStr.append(dmsStrFromDeg(deg, precision=prec))
				print "[%r, %r, 1, %r, %r, %r, %r, %r]," % (testStr, commentStr, itemList, deg, sec, neatStr, outDMSStr)
			except StandardError, e:
				print "unexpected failure on %r (%s); error = %s" % (testStr, commentStr, e)
		else:
			print "[%r, %r, 0, %r, %r, %r, %r, %r]," % tuple([testStr, commentStr] + [None]*5)

if __name__ == "__main__":
	doPrint = 0
	if doPrint:
		_printTest()
	else:
		_assertTest()
