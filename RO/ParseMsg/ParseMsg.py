#!/usr/local/bin/python
"""Parses a message of the form: header keywordValueData
returning a dictionary.

2002-12-16 ROwen	Renamed parseMsg to parseHubMsg and rewrote to call parseKeyValueData
2003-11-19 ROwen	Added "noValKey=" to test cases as it caused an infinite loop.
2004-05-18 ROwen	Removed import GetHeader; from GetHeader import... was being used instead.
					Modified test code to use astr instead of str.
"""
from GetKeyword import getKeyword
from GetValues import getValues
from GetHeader import getHubHeader
from ParseData import parseKeyValueData
from RO.Alg.OrderedDict import OrderedDict

def parseHubMsg(astr):
	"""Parses one message of the form:
		cmdr cmdID actor type keyword1=value11, value12,...; keyword2=value21, value22...
	returning a dictionary.

	Inputs:
	- astr: the string to parse, in the form:
		cmdr cmdID actor type keyword1=value11, value12,...; keyword2=value21, value22...

	Returns a dictionary containing items:
		- "cmdr": commander (string)
		- "cmdID": command ID number (integer)
		- "actor": actor (string)
		- "type": type of message (character)
		- "dataStart": starting index of data in astr,
		- "data": dataDict, as returned by parseKeyValueData(astr[dataStart:]),
		- "msgStr": astr,
	
	For details of the header format, please see ParseHeader:getHubHeader
	For details of the keyword/value format and the returned dataList,
	please see ParseData:parseKeyValueData	
	"""
	# start the message dictionary by extracting the header from astr;
	# this also returns the index to the next item (start of data) in astr
	# or None if no data
	msgDict, dataStart = getHubHeader(astr)

	# coerce message type to lowercase
	msgDict["type"] = msgDict["type"].lower()
	
	# extract data
	msgDict['dataStart'] = dataStart
	msgDict['data'] = parseKeyValueData(astr[dataStart:])
	
	# include full message string
	msgDict['msgStr'] = astr
		
	return msgDict


if __name__ == '__main__':
	# perform test
	print "testing parseHubMsg\n"
	testList = [
		"me 123 tcc > keyword = ; key2 =",
		"me 123 tcc > keyword",
		"other -78 tcc i",
		"me 123 tcc : strSet='str1', 'str2'",
		"me 123 tcc : genSet=1, 2, 3.14159, 'str4', 'str5'",
		"me 123 dis : noValKey1; intKey2=2; noValKey3",
		"me 123 tcc > noValueKey=",
		"me 1 tcc badType_NotOneChar",
		"me tcc missingCmdID",
	]
	for astr in testList:
		try:
			msgDict = parseHubMsg(astr)
			print "parseHubMsg('%s') = %s" % (astr, repr(msgDict))
		except StandardError, e:
			print "failed with error: ", e
