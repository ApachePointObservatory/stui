#!/usr/local/bin/python
"""procFiles calls a user-supplied function "func" to process a set of files one by one.
The processed data is typically concatenated into one output file, but this behavior
is controlled by outPath.

Inputs:
- func: the function to apply; more information below.
- inPathList: a list of file (full path) names
  sys.argv[1:] by default (the list of files dropped on a droplet)
- outDir: the output directory. If none or "" the default directory is used.
- outFile: the output file.
  - if None, the user is asked for a file name
    (on a Mac this is done via a standard dialog box)
    and standard output is redirected
    (use if the output from multiple files is to go to one file)
  - if "" then standard output is left alone
    (use this for debugging or if your process opens its own output file(s))
  - if a file, standard output is set to this file
    (use if the output from multiple files is to go to one file)
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

Returns outPath, a combination of outDir and outFile.

Pattern special characters are those for fnmatch:
*		match any sequence of 0 or more characters
?		match any single character
[seq]	matches any character in seq
[!seq]	matches any character not in seq

Here is detailed information about "func", the user-supplied function.

"func" must have the following arguments (all inputs):
- inPath: the full path name of the input file;
	this is for information only; procFiles has already opened the file
	and redirected standard input to it
- isFirst: true if this is the first file of the list, false otherwise
- isLast: true if this is the last file of the list, false otherwise
- outPath: the combination of the output directory and output file
  (with defaults or user requests filled in);
  if outFile is "" then outPath only includes outDir and is a directory.
  
	  

"func" is called once for each input file. It is expected to process the entire file
before returning (more on this below). 

EXAMPLE 1: ALL OUTPUT TO ONE FILE
In this case procFiles manages the output file for you
and all you have to do is write to standard output.

Your function should:
* Read data from standard input until end-of-file (readline returns "")
* Write data to standard output (the output file is managed by procFiles)
* Write messages (if any) to standard error

Error handling:
* Processing stops for keyboard interrupt or sys.exit.
* On RuntimeError, a message is printed and the next file is processed.
  This is useful to report an expected error such as bad data format.
* For other exceptions a traceback is printed and the next file is processed.
  This is good for unexpected errors.

Here is a template:

import sys, procFiles
def func(inPath, isFirst, isLast, outPath)
	if isFirst:
		# write output header data here (via print or sys.stdout.write)
	for data in sys.stdin:
		# process the current line of input data
		# and write output data (via print or sys.stdout.write)
		# raise RuntimeError if data cannot be processed
	if isLast:
		# write output footer data here (via print or sys.stdout.write)
procFiles.procFiles(func)

EXAMPLE 2: EACH FILE'S OUTPUT GOES TO A SEPARATE FILE
In this case you must open, write to and close the output files yourself.
Other than that, your function behaves as in example 1.

Here is a template:

import sys, procFiles
def func(inPath, isFirst, isLast, outPath):
	# generate the output file
	myOutName = "foo"
	myOutPath = os.path.join(outPath, myOutName)
	
	# you can write directly to the file or redirect stdout;
	# here is an example of the latter:
	sys.stdout = open(outPath, "w")
	
	# it is safest to close the files yourself; try/finally works nicely for this:
	try:
		if isFirst:
			# write output header data here (via print or sys.stdout.write)
		for data in sys.stdin:
			# process the current line of input data
			# and write output data (via print or sys.stdout.write)
		if isLast:
			# write output footer data here (via print or sys.stdout.write)
	finally:
		sys.stdout.close()
procFiles.procFiles(func, outFile="")

Hint: if you wish to break inPath up into the file name and/or directory, use the following code:
	import os.path
	inName = os.path.basename(inPath)
	inDir = os.path.dirname(inPath)

History:
1.0 11/28/00 Russell Owen, UW/ARC. First public release.
	Compatible with Python 1.5.2 and 2.0.
1.1 12/14/00 bug fix: was writing some informational data to the output file.
2.0 2001-10-29 Russell Owen: split outPath argument into outDir and outFile
	and added outPath argument to the user function.
2.1 2001-11-09 Russell Owen: minor bug fix: cancelling the output file dialog
	would send output to stdout instead of quitting.
2.2 2001-11-20 Russell Owen: minor fixes to the examples in this header; no code changes.
2.3 2003-04-11 Russell Owen: added patterns and recurseDirs args;
	bug fix: isFirst and isLast not set properly
	if the first or last file was a not a text file
2.4 2003-04-18 Russell Owen: bug fix: was not checking patterns correctly;
	modified to use RO.OS.expandFileList.
2003-11-18 ROwen	Modified to use SeqUtil instead of MathUtil.
2003-12-15 ROwen	Bug fix: changed one RO. to RO.SeqUtil.
					Modified to open input files in universal newline mode.
					Modified to use EasyDialogs instead of macfs for output dialog.
2004-02-06 ROwen	Changed recurseDirs to recursionDepth and added exclPatterns.
2004-03-05 ROwen	Made compatible with Python 2.2.x again by opening files
					in universal newline mode only if available
2005-03-01 ROwen	Removed use of (deprecated) xreadlines in the docs.
					Continue on error; report traceback unless RuntimeError.
2005-03-15 ROwen	Bug fix: was setting outPath to "" instead of outDir if outFile="".
"""
import fnmatch
import types
import os.path
import sys
import traceback
import RO.OS
import RO.SeqUtil

def procFiles (
	func,
	inPathList = sys.argv[1:],
	outDir = None,
	outFile = "",
	patterns = None,
	recursionDepth = None,
):
	# make sure func is callable
	if not callable(func):
		raise RuntimeError, "supplied function is not callable"

	# handle case of inPathList being a single string
	inPathList = RO.SeqUtil.asSequence(inPathList)
	
	# Recurse into directories, choosing files that match the pattern
	# rejecting nonexistent files with a message to stderr
	# and filtering out duplicates.
	# Doing this ahead of time means we can reliably sense the first and last file
	# and reliably count the files.
	inPathList = RO.OS.findFiles(
		paths = inPathList,
		patterns = patterns,
		recursionDepth = recursionDepth,
		patWarn=True,
	)

	# print # of files; quit if 0
	nFiles = len(inPathList)
	if nFiles < 1:
		sys.stderr.write("No files; quitting\n")
		return
	elif nFiles == 1:
		sys.stderr.write("1 file to process\n")
	else:
		sys.stderr.write("%d files to process\n" % len(inPathList))


	# check outDir or fill in default
	if outDir:
		if not os.path.exists(outDir):
			raise RuntimeError, "directory %r does not exist" % (outDir,)
	else:
		outDir = os.curdir
	
	# open outFile (if outFile is None, ask user for output file first)
	if outFile == None:
		# ask user for output file name
		try:
			import EasyDialogs
			outPath = EasyDialogs.AskFileForSave(
				message = 'File for output',
				defaultLocation = outDir,
				fileType = 'TEXT',
			)
			if outPath == None:
				return

			sys.stdout = file(outPath, 'w')
		except ImportError:
			# unknown platform; use standard prompt
			outFile = raw_input(
				"output file relative to %r [stdout]: " % outDir)

			# generate outPath, and if it's a file, open it and redirect stdout
			if outFile:
				outPath = os.path.join(outDir, outFile)
				sys.stdout = file(outPath, 'w')
			else:
				outPath = outDir
	elif outFile:
		outPath = os.path.join(outDir, outFile)
		sys.stdout = file(outPath, 'w')
	else:
		outPath = outDir
	
	# stdout now points to outfile; make sure to undo this
	try:
		# loop over input files; continue with the next file if one fails
		isFirst = True
		for inPath in inPathList:
			sys.stderr.write("\nProcessing file: %r\n" % inPath)
	
			try:
				try:
					# open input file (in universal newline mode if possible) and redirect input
					sys.stdin = RO.OS.openUniv(inPath)
	
					# call user-supplied function to process file
					isLast  = (inPath == inPathList[-1])
					func(inPath, isFirst, isLast, outPath)
					isFirst = False
				finally:
					# close input file and restore standard input
					if sys.stdin != sys.__stdin__:
						sys.stdin.close()
						sys.stdin = sys.__stdin__
			except (KeyboardInterrupt, SystemExit):
				sys.stderr.write ("Aborted during file %r\n" % (inPath,))
				break
			
			except RuntimeError, err:
				sys.stderr.write ("Failed on file %r with error: %s\n" % (inPath, err))
	
			except Exception:
				sys.stderr.write ("Failed on file %r with error:\n" % (inPath,))
				traceback.print_exc(file=sys.stdout)
	
	finally:
		# close output file and restore standard output
		if sys.stdout != sys.__stdout__:
			sys.stdout.close()
			sys.stdout = sys.__stdout__

	sys.stderr.write("Finished\n")
	return outPath


def testFunc (fName, isFirst=False, isLast=False, outPath=""):
	# read from stdin (fName is just informational)
	# write parsed data to stdout
	# write informational messages to stderr
	# if you throw an error, processing will continue with the next file

	# this test function simply prints the listed files,
	# each with a brief header and footer

	# echo arguments, just to show what's happening
	sys.stderr.write ("testFunc called with fName=%s, outPath=%s, isFirst=%d, isLast=%d\n" %
		(fName, outPath, isFirst, isLast))

	if isFirst:
		print "***** Beginning of all files *****\n"

	# echo line of file
	while True:
		data = sys.stdin.readline ()
		if data == "":
			break
		sys.stdout.write(data)

	if isLast:
		print "***** End of all files *****\n"

if __name__ == '__main__':
	# test self on self
	outPath = procFiles (testFunc, 'procFiles.py', "")
