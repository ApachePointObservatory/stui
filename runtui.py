#!/usr/bin/python
"""Launch TUI, the APO 3.5m telescope user interface.

Location is everything:
This script's directory is automatically added to sys.path,
so having this script in the same directory as RO and TUI
makes those packages available without setting PYTHONPATH.

History:
2004-05-17 ROwen	Bug fix: automatic ftp hung due to import lock contention,
					because execution was part of importing.
					Fixed by first importing TUI.Main and then running the app.
2006-02-28 ROwen	Log messages to a file in current directory, if possible.
"""
import os
import sys

OldLogName = "oldtuilog.txt"
LogName = "tuilog.txt"

# try to open a new log file
# (after closing any existing file)
# don't sweat it if it fails
errLog = None
try:
	if os.path.isfile(LogName):
		if os.path.isfile(OldLogName):
			os.remove(OldLogName)
		os.rename(LogName, OldLogName)
	errLog = file(LogName, "w")
except OSError, e:
	sys.stderr.write("Could not open log file: %s\n" % (e,))

try:
	if errLog:
		sys.stdout = errLog
		sys.stderr = errLog
		import time
		from TUI.Version import VersionStr
		startTimeStr = time.strftime("%Y-%m-%dT%H:%M:%S")
		errLog.write("TUI %s started %s\n" % (VersionStr, startTimeStr))
	
	import TUI.Main
	TUI.Main.runTUI()
finally:	
	if errLog:
		errLog.close()
