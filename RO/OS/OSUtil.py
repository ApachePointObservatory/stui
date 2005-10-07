#!/usr/local/bin/python
from __future__ import generators
"""Operating system utilities

History:
2003-03-21 ROwen	splitPath
2003-03-24 ROwen	added walkDirs
2003-04-18 ROwen	added expandFileList; added patWarn arg. to walkDirs.
2003-11-18 ROwen	Modified to use SeqUtil instead of MathUtil.
2004-02-04 ROwen	Renamed to OSUtil and moved into the OS package;
					added expandPath, realPath and removeDupPaths.
2004-02-05 ROwen	Added exclPatterns to walkDirs.
2004-02-06 ROwen	Combined walkDirs and expandPathList into findFiles
					and changed recurseDirs to recursionDepth.
2004-05-18 ROwen	Modified splitPath to use var end (it was computed but ignored).
2005-08-02 ROwen	Added getResourceDir
2005-10-07 ROwen	splitPath bug fix: on Windows the first element
					(disk letter) included a backslash.
"""
import os.path
import sys
import fnmatch
import RO.SeqUtil

def expandPath(path):
	"""Returns an expanded version of path:
	- follows symbolic links (but not Mac or Windows aliases)
	- expands to a normalized absolute path
	- puts the path into a standard case
	"""
	return os.path.normcase(os.path.abspath(realPath(path)))

"""Define a version of os.path.realpath that is available on all platforms.
realPath(path) returns the path after expanding all symbolic links.
Note: does NOT follow Mac or Windows aliases.
"""
try:
	realPath = os.path.realpath
except AttributeError:
	def realPath(path):
		return path

def findFiles(paths, patterns=None, exclPatterns=None, returnDirs=False, recursionDepth=None, patWarn=False):
	"""Search for files that match a given pattern,	returning a list of unique paths.
	
	paths may include files and/or directories.
	- All directories that are on the list are searched for files
	 (and so on recursively to the specified depth).
	- Any files in paths or that are found while searching
	  are included in the output list *if* they match the patterns
	  (this includes directories if returnDirs is true).
	
	One use for this is to handle a list of files that has been
	dragged and dropped on an applet.

	Inputs:
	- paths: one or more paths; files are checked to see if they match
		the specified pattern and directories are searched
		if they don't exceed the recursion level
	- patterns: one or more patterns the file name must match;
		is omitted, all files are matched.
		Patterns are matched using fnmatch, which does unix-style matching
		(* for any char sequence, ? for one char).
	- exclPatterns: one or more patterns the file name must not match;
		if omitted, nothing is excluded
	- recursionDepth: recursion level; None or an integer n:
		None means infinite recursion
		n means go down n levels from the root path, for example:
		0 means don't even look inside directories in paths
		1 means look inside directories in paths but no deeper
	- returnDirs: should directories be included in the returned list?
	- patWarn: print names of files that don't match the pattern to stderr
	
	Pattern special characters are those for fnmatch:
	*		match any sequence of 0 or more characters
	?		match any single character
	[seq]	matches any character in seq
	[!seq]	matches any character not in seq

	Note: EVERY directory that is found is searched (if the recursion level
	is not exhausted). Whether a directory is searched has nothing to do with
	patterns, exclPatterns or returnDirs.
	"""
	# process the inputs
	paths = RO.SeqUtil.asSequence(paths)
	patterns = patterns or ("*",)
	patterns = RO.SeqUtil.asSequence(patterns)
	exclPatterns = exclPatterns or ()
	exclPatterns = RO.SeqUtil.asSequence(exclPatterns)
	if recursionDepth == None:
		recursionDepth = _Inf()
	else:
		recursionDepth = int(recursionDepth)

	# perform the search
	foundPathList = []
	for path in paths:
		isFile = os.path.isfile(path)
		isDir = os.path.isdir(path)
		if isFile or (returnDirs and isDir):
			if _nameMatch(path, patterns, exclPatterns):
				foundPathList.append(path)
			elif patWarn:
				sys.stderr.write("Skipping %r: no pattern match\n" % (path,))

		if isDir:
			# directory: recurse into it if depth not exceeded
			if recursionDepth > 0:
				foundPathList += list(_findFilesIter(
					dirPath = path,
					patterns = patterns,
					exclPatterns = exclPatterns,
					returnDirs = False,
					recursionDepth = recursionDepth - 1,
					patWarn = patWarn,
				))
		elif not isFile:
			# bad path or something weird
			if not os.path.exists(path):
				sys.stderr.write("Warning: file does not exist: %s\n" % path)
			else:
				sys.stderr.write("Warning: skipping mysterious non-file, non-directory: %s\n" % path)
			continue
	
	return removeDupPaths(foundPathList)

def getResourceDir(pkg, *args):
	"""Return a directory of resources for a package,
	assuming the following layout:
	
	- For the source code, the resource directory
	is in <pkgRoot>/pkg/arg0/arg1...
	- For a binary distribution, the package is in
	<distRoot>/<something>.zip/pkg
	and the resources are in
	<distRoot>/pkg/arg0/arg1/...

	Example: consider the package RO containing resource directory Bitmaps.
	When you make a binary distribution, RO will go in <distRoot>/Modules.zip
	So long as you put Bitmaps in <distRoot>/RO/Bitmaps
	then the following will find it in the source and binary distribution:
    getResourceDir(RO, "Bitmaps")
	"""
	pkgRoot = os.path.dirname(os.path.dirname(pkg.__file__))
	if pkgRoot.lower().endswith(".zip"):
		pkgRoot = os.path.dirname(pkgRoot)
	return os.path.join(pkgRoot, pkg.__name__, *args)

def removeDupPaths(pathList):
	"""Returns a copy of pathList with duplicates removed.

	To compare two paths, both are first resolved as follows:
	- follows symbolic links (but not Mac or Windows aliases)
	- expands to a normalized absolute path
	- puts into a standard case
	However, the original path names are used in the returned
	list (and the original order is preserved, barring duplicates).
	"""


	expDict = {}
	outList = []
	for path in pathList:
		expPath = expandPath(path)
		if expPath not in expDict:
			expDict[expPath] = None
			outList.append(path)
	return outList

def splitPath(path):
	"""Splits a path into its component pieces.
	Similar to os.path.split but breaks the path completely apart
	instead of into just two pieces.
	
	My code with a correction from a Python Cookbook recipe by Trent Mick
	
	Note: pathList is built backwards and then reversed because
	inserting is much more expensive than appending to lists.
	"""
	pathList = []
	while True:
		head, tail = os.path.split(path)
		if "" in (head, tail):
			end = head or tail
			if end.endswith(os.sep):
				end = end[:-1]
			if end:
				pathList.append(end)
			break
			
		pathList.append(tail)
		path = head
	pathList.reverse()
	return pathList

def openUniv(path):
	"""Opens a text file for reading in universal newline mode, if possible;
	silently opens without universal mode for Python versions < 2.3.
	"""
	if sys.version_info[0:2] >= (2,3):
		# use universal newline support (new in Python 2.3)
		openMode = 'rU'
	else:
		openMode = 'r'
	return open(path, openMode)

def _findFilesIter(dirPath, patterns, exclPatterns=(), returnDirs=False, recursionDepth=None, patWarn=False):
	"""Helper function for findFiles that does most of the work.
	Allows findFiles to clean up patterns once, instead of for every recursion.
	
	Assumes dirPath is the path to an existing directory.
	Never returns dirPath itself!
	"""
#	print "_findFilesIter(%r, %r, %r, %r, %r, %r)" % (dirPath, patterns, exclPatterns, returnDirs, recursionDepth, patWarn)
	# check each file
	for baseName in os.listdir(dirPath):
		fullPath = os.path.normpath(os.path.join(dirPath, baseName))
		
		# grab if it matches our pattern and entry type
		if os.path.isfile(fullPath) or returnDirs:
			if _nameMatch(baseName, patterns, exclPatterns):
				yield fullPath
			elif patWarn:
				sys.stderr.write("Skipping %r: no pattern match\n" % (fullPath,))
				
		# recursively scan other folders, appending results
		if recursionDepth > 0 and os.path.isdir(fullPath):
			for x in _findFilesIter(
				dirPath = fullPath,
				patterns = patterns,
				exclPatterns = exclPatterns,
				returnDirs = returnDirs,
				recursionDepth = recursionDepth - 1,
				patWarn = patWarn,
			):
				yield x

class _Inf:
	def __gt__(self, other):
		return True
	def __ge__(self, other):
		return True
	def __eq__(self, other):
		return isinstance(other, _Inf)
	def __ne__(self, other):
		return not isinstance(other, _Inf)
	def __le__(self, other):
		return isinstance(other, _Inf)
	def __lt__(self, other):
		return False
	def __add__(self, other):
		return self
	def __sub__(self, other):
		return self
	def __mul__(self, other):
		return self
	def __div__(self, other):
		return self
	def __str__(self):
		return "inf"
	def __int__(self):
		return self
	def __long__(self):
		return self
	def __float__(self):
		return self

def _nameMatch(path, patterns, exclPatterns):
	"""Check if file name matches a set of patterns.
	
	Returns True if baseName matches any pattern in patterns
	and does not match any pattern in exclPatterns.
	Matching is done by fnmatch.fnmatch.
	
	Does no verification of any input.
	"""
#	print "_nameMatch(%r, %r, %r)" % (path, patterns, exclPatterns)
	baseName = os.path.basename(path)
	for pat in patterns:
		if fnmatch.fnmatch(baseName, pat):
			for exclPat in exclPatterns:
				if fnmatch.fnmatch(baseName, exclPat):
					return False
			return True
	return False	
