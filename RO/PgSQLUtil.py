#!/usr/local/bin/python
"""Utility functions for working with SQL databases
and with data files in FMPro "merge" format.

Specific to PostgreSQL, though most code is common to the
Python Database 2.0 format <http://www.python.org/topics/database/DatabaseAPI-2.0.html>.

2003-12-15 ROwen
"""
import time

_DataSepStr = '","'
_ArraySepStr = chr(29)

class FieldDescr:
	"""A description of a data field in a database. At present this is primarily used
	to convert data from a text file to data in a form suitable for importing into a database.
	"""
	def __init__(self, fieldName, cnvFunc=str, blankOK=False, blankVal=None, isArray=False, arraySep=_ArraySepStr):
		"""Create a new database field descriptor.
		
		Inputs:
		- fieldName: the name of the field, as given in the database
		- cnvFunc: the function to convert a string value to the final value;
			for an array, this function is applied to each element in turn;
			cnvFunc takes one argument (a string) and returns the converted value;
			cnvFunc will never see a blank string
		- blankOK: if true, blank strings ('') are acceptable, else they raise an exception
		- blankVal: if blankOK true, this is the converted value for ('')
		- isArray: an array of values
		- arraySep: the array separator
		"""
		self.fieldName = fieldName
		self.cnvFunc = cnvFunc
		self.blankOK = blankOK
		self.blankVal = blankVal
		self.isArray = isArray
		self.arraySep = arraySep
	def _scalarValFromStr(self, strVal):
		"""Convert one scalar value. Like valFromStr but if the field is an array,
		converts just one element of the array.
		"""
		if strVal:
			try:
				return self.cnvFunc(strVal)
			except Exception, e:
				raise ValueError, "Could not convert %s: %s" % (strVal, e)
		elif self.blankOK:
			return self.blankVal
		else:
			raise ValueError, "%s is empty" % (self.fieldName,)
	def valFromStr(self, strVal):
		"""Convert the string value of this field to the final value.
		If the field is an array, it is split and the conversion function
		is applied to each elemement in turn.
		"""
		if self.isArray:
			return [self._scalarValFromStr(itemStrVal) for itemStrVal in strVal.split(self.arraySep)]
		else:
			return self._scalarValFromStr(strVal)
		

def dateToDBFmt(strVal, fromFmt="%m/%d/%Y"):
	"""Convert a date from the specified fromFmt (a string accepted by time.strptime)
	to "yyyy-mm-dd", the format used by databases.
	"""
	try:
		dateTuple = time.strptime(strVal, fromFmt)
	except ValueError:
		raise ValueError, "%s not in the specified date format: %s" % (strVal, fromFmt)
	return time.strftime("%Y-%m-%d", dateTuple)


def dataDictFromStr(line, fieldDescrList, fieldSep=_DataSepStr):
	"""Converts a set of string values for fields into a data dictionary;
	The data is given as a list of fields, in the order specified by fieldDescrList
	and separated by fieldSep;
	
	The defaults are appropriate to FileMaker Pro "merge" format.
	
	Inputs:
	- fieldDescrList: a list of FieldDescr objects, one per field
	- fieldSep: string that separates values for each field

	Note: every entry in "line" must be described in the fieldDescrList
	"""

	# split the line up, trimming off the leading " and trailing :\n
	dataArry = line[1:-2].split(_DataSepStr)
	assert(len(dataArry) == len(fieldDescrList), "could not parse data\n%s" % (line,))
	
	dataDict = {}
	for ind in range(len(fieldDescrList)):
		fieldDescr = fieldDescrList[ind]
		strVal = dataArry[ind]
		dataDict[fieldDescr.fieldName] = fieldDescr.valFromStr(strVal)
	return dataDict


def rowExists(dbCursor, table, dataDict, fieldsToCheck):
	"""Checks to see if row exists with matching values in the specified fields.
	Returns True or False.
	"""
	# generate the sql command:
	# select * from table where (fieldName1=%(fieldName1)s, fieldName2=%(fieldName2)s,...)
	fmtFieldList = ["(%s=%%(%s)s)" % (fieldName, fieldName) for fieldName in fieldsToCheck]
	fmtFieldStr = " and ".join(fmtFieldList)
	sqlCmd = "select * from %s where %s" % (table, fmtFieldStr)
	
	# execute the command; if any rows found, the row exists
	dbCursor.execute(sqlCmd, dataDict)
	result = dbCursor.fetchone()
	return bool(result)


def getLastInsertedID(dbCursor, table, primKeyName):
	"""Returns the primary key for the last inserted row.
	Returns None if no row inserted.
	This code is database-specific because every database seems to handle this differently
	(it's a pity there's no common API for this common task).
	"""
	lastOID = dbCursor.oidValue
	if lastOID == None:
		return None
	sqlCmd = "select %s from %s where oid = %s" % (primKeyName, table, lastOID)
	dbCursor.execute(sqlCmd)
	result = dbCursor.fetchone()
	if not result:
		return None
	return result[0]


def insertRow(dbCursor, table, dataDict, fieldsToAdd, fieldsToCheck=None):
	"""Inserts a row of data into the specified table in a database.
	Should raise an exception if it fails--does it do so reliably?
	"""
	# if fieldsToCheck specified, make entry with matching fields exists
	if fieldsToCheck and rowExists(dbCursor, table, dataDict, fieldsToCheck):
		raise RuntimeError, "a matching entry already exists"
	
	addFieldStr = ", ".join(fieldsToAdd)
	addValueList = ["%%(%s)s" % (fieldName,) for fieldName in fieldsToAdd]
	addValueStr = ", ".join(addValueList)
	sqlCmd = "insert into %s (%s) values (%s)" % (table, addFieldStr, addValueStr)
	# print "executing:", sqlCmd
	dbCursor.execute(sqlCmd, dataDict)


def insertMany(dbCursor, table, dataDict, arrayFields, scalarFields=None):
	"""Inserts multiple rows into the specified table of a database.
	Should raise an exception if it fails--does it do so reliably?
	
	Inputs:
	- dbCursor: a database cursor
	- table: the name of the table
	- dataDict: the data, with field names as keys
	- arrayFields: a list of fields to add whose values are arrays;
		every array must have the same length;
		one row will be added for each array element
	- scalarFields: a list of fields to add whose values are scalars;
		these fields will have the same value for every added row
		
	Returns the number of rows added.
	"""
	scalarFields = scalarFields or []

	# check lengths
	numEntries=0
	for fieldName in arrayFields:
		if numEntries:
			if len(dataDict[fieldName]) != numEntries:
				raise ValueError, "arrays must have matching length"
		else:
			numEntries = len(dataDict[fieldName])
	if numEntries == 0:
		return 0
	
	# convert the data to the form of a list of tuples, one per row,
	# with values in the same order as allFields = scalarFields + arrayFields
	listOfLists = [[dataDict[fieldName]]*numEntries for fieldName in scalarFields] \
		+ [dataDict[fieldName] for fieldName in arrayFields]
	zippedList = zip(*listOfLists)
	allFields = scalarFields + arrayFields
	
	# set up the query as:
	# insert into <table> (<fieldName1>, <fieldName2>,...) values (%s, %s,...)
	# note: (%s, %s, ...) is just a comma-separated set of "%s"s, one per field
	sListStr = ", ".join("%%s" * len(allFields)) # "%s, %s, ..." one per field
	fieldListStr = ", ".join(allFields) # "fieldName1, fieldName2, ..."
	sArry = ("%s, " * len(allFields))[:-2]
	sqlCmd = "insert into %s (%s) values (%s)" % (table, fieldListStr, sArry)
	
	# execute the insert
	dbCursor.executemany(sqlCmd, zippedList)
	return numEntries
