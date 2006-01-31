#!/usr/local/bin/python
"""Utility functions for working with SQL databases
and with data files in FMPro "merge" format.

Tested with pyPgSQL (for PostgreSQL) and MySQLdb (for MySQL).

2003-12-15 ROwen
2005-06-08 ROwen	Changed FieldDescr to a new-style class.
2005-07-05 ROwen	Added some error checking and reporting to dataDictFromStr.
					Fixed a nonfunctional assert statement in insertRow.
2005-11-14 ROwen	Renamed module from PgSQLUtil to SQLUtil.
					Renamed getLastInsertedID to getLastInsertedIDPgSQL.
					Added getLastInsertedIDMySQL.						
2005-12-13 ROwen	Mod. insertRow so fieldsToAdd defaults to all fields.
					Mod. rowExists so fieldsToCheck defaults to all fields.
					Added NullDBConn, NullDBCursor, for testing database code
					without actually modifying databases.
					Added formatFieldEqVal to help generate select commands.
2006-01-17 ROwen	formatFieldEqVal: added sepStr argument.
2006-01-20 ROwen	Removed getLastInsertedIDMySQL since it didn't work as advertised;
					use the cursor's lastrowid instead; for more information, see the MySQLDb manual
					entry for insert_id(). (Note: despite the 1.2.0 manual, insert_id() is an attribute
					of the connection, but is used to create the cursor's lastrowid.)
2006-01-31 ROwen	Added rowcount, lastrowid to NullDBCursor.
"""
import time

_DataSepStr = '","'
_ArraySepStr = chr(29)

class FieldDescr(object):
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
	if len(dataArry) != len(fieldDescrList):
		raise RuntimeError("Bad data length; %s data items != %s field descriptors in line:\n%r\n" % \
			(len(dataArry), len(fieldDescrList), line)
		)
	
	dataDict = {}
	for ind in range(len(fieldDescrList)):
		fieldDescr = fieldDescrList[ind]
		try:
			strVal = dataArry[ind]
		except IndexError:
		
			print "fieldDescrList(%s)=%s" % (len(fieldDescrList), fieldDescrList)
			print "dataArry(%s)=%s" % (len(dataArry), dataArry)
			raise
		dataDict[fieldDescr.fieldName] = fieldDescr.valFromStr(strVal)
	return dataDict


def formatFieldEqVal(fieldNames, sepStr = " and "):
	"""Format a (field1=value1) and (field2=value2)... clause
	in the form used with a data dictionary.
	This is intended to help generate select commands.
	
	Inputs:
	- fieldNames: a list or other sequence of field names
	- sepStr: the string to separate field=value pairs.
	
	Example:
	sqlCmd = "select * from %s where %s" % (tableName, formatFieldEqVal(fieldNames))
	dbCursor.execute(sqlCmd, dataDict)
	"""
	fmtFieldList = ["(%s=%%(%s)s)" % (fieldName, fieldName) for fieldName in fieldNames]
	return sepStr.join(fmtFieldList)


def getLastInsertedIDPgSQL(dbCursor, table, primKeyName):
	"""Return the primary key for the last inserted row for a PostgreSQL database.
	Returns None if no row inserted.

	Inputs:
	- dbCursor: database cursor
	- table: name of table
	- primKeyName: name of primary key field
	
	Database-specific because every database seems to handle this differently.
	For MySQLDb see the documentation for dbCursor.last_insert_id().
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

def insertRow(dbCursor, table, dataDict, fieldsToAdd=None, fieldsToCheck=None):
	"""Insert a row of data into the specified table in a database.
	
	Inputs:
	- dbCursor: database cursor
	- table: name of table
	- dataDict: dict of field name: value entries
	- fieldsToAdd: a list of fields to set; if None (default) then all fields in are set
	- fieldsToCheck: a list of fields to check for a duplicate entry:
	    if there is a row in the table where all fieldsToCheck fields
	    match dataDict, then raise RuntimeError and do not change the database.
	    If None or some other false value then do not check.

	Should raise an exception if it fails--does it do so reliably?
	"""
	# if fieldsToCheck specified, make sure an entry with matching fields does not already exist
	if fieldsToCheck and rowExists(dbCursor, table, dataDict, fieldsToCheck):
		raise RuntimeError, "a matching entry already exists"
	
	if fieldsToAdd == None:
		fieldsToAdd = dataDict.keys()
	
	addFieldStr = ", ".join(fieldsToAdd)
	addValueList = ["%%(%s)s" % (fieldName,) for fieldName in fieldsToAdd]
	addValueStr = ", ".join(addValueList)
	sqlCmd = "insert into %s (%s) values (%s)" % (table, addFieldStr, addValueStr)
	#print "executing:", sqlCmd
	dbCursor.execute(sqlCmd, dataDict)


def insertMany(dbCursor, table, dataDict, arrayFields, scalarFields=None):
	"""Insert multiple rows into the specified table of a database.
	Should raise an exception if it fails--does it do so reliably?
	
	Inputs:
	- dbCursor: database cursor
	- table: name of table
	- dataDict: dict of field name: value entries
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


def rowExists(dbCursor, table, dataDict, fieldsToCheck=None):
	"""Check to see if row exists with matching values in the specified fields.
	Returns True or False.
	
	Inputs:
	- dbCursor: database cursor
	- table: name of table
	- dataDict: dict of field name: value entries
	- fieldsToCheck: list of fields to check; if None (default) then check all fields
	"""
	if fieldsToCheck == None:
		fieldsToCheck = dataDict.keys()

	# generate the sql command:
	# select * from table where (fieldName1=%(fieldName1)s, fieldName2=%(fieldName2)s,...)
	sqlCmd = "select * from %s where %s" % (table, formatFieldEqVal(fieldsToCheck))
	
	# execute the command; if any rows found, the row exists
	dbCursor.execute(sqlCmd, dataDict)
	result = dbCursor.fetchone()
	return bool(result)


class NullDBCursor (object):
	"""A fake database cursor for testing database code.
	
	This likely does not support the entire database cursor interface,
	but does support everything used by RO.SQLUtil.
	
	It prints out the SQL commands that would be executed.
	"""
	def __init__(self, db):
		self.db = db

		self.oidValue = 1
		self.rowcount = 1
		self.lastrowid = 1

	def execute(self, sqlCmd, dataDict=None):
		print "%s.execute %s" % (self, sqlCmd)
		if dataDict:
			keys = dataDict.keys()
			keys.sort()
			for key in keys:
				print "  %s = %s" % (key, dataDict[key])
	
	def fetchone(self):
		return [1]
	
	def executemany(self, sqlCmd, aList):
		print "%s.executemany %s" % (self, sqlCmd)
		for item in aList:
			print "  %s" % (item,)
	
	def __repr__(self):
		return "NullDBCursor(db=%s)" % (self.db,)


class NullDBConn (object):
	"""A fake database connection for testing database code.
	
	Example:
	import MySQLdb
	import RO.SQLUtil
	TestOnly = True
	if TestOnly:
		connect = RO.SQLUtil.NullDBConn
	else:
		connect = MySQLdb.connect
	dbConn = connect(user=..., db=..., ....)
	
	This likely does not support the entire database connection interface,
	but does support everything used by RO.SQLUtil.
	"""
	def __init__(self, user=None, db=None, passwd=None, **kargs):
		self.user = user
		self.db = db
		self.kargs = kargs

		self.isOpen = True
		print self

	def cursor(self):
		return NullDBCursor(db = self.db)
	
	def commit(self):
		print "%s.commit" % (self,)
	
	def rollback(self):
		print "%s.rollback" % (self,)
	
	def close(self):
		self.isOpen = False
		print "%s.close" % (self,)
	
	def __str__(self):
		return "NullDBConn(db=%s; user=%s)" % (self.db, self.user)
		
	def __repr__(self):
		if self.isOpen:
			state = "open"
		else:
			state = "closed"
		return "NullDBConn(user=%s, db=%s, %s) (%s)" % (self.user, self.db, self.kargs, state)