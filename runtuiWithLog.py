#!/usr/bin/env python
"""Launch TUI, the APO 3.5m telescope user interface.

Location is everything:
This script's directory is automatically added to sys.path,
so having this script in the same directory as RO and TUI
makes those packages available without setting PYTHONPATH.

History:
2004-05-17 ROwen    Bug fix: automatic ftp hung due to import lock contention,
                    because execution was part of importing.
                    Fixed by first importing TUI.Main and then running the app.
2006-03-06 ROwen    Branch standard runtui.py; this version redirects stderr
                    to a log file in docs directory, if possible.
2007-01-23 ROwen    Changed #!/usr/local/bin/python to #!/usr/bin/env python
2008-01-29 ROwen    Modified to add ../tcllib to TCLLIBPATH on MacOS X;
                    this simplies the use of the built-in Tcl/Tk in the Mac package.
2009-02-24 ROwen    Modified to name log files by UTC date and to save 10 old log files.
"""
import glob
import os
import sys
import time
import traceback

LogPrefix = "tuilog"
LogSuffix = ".txt"
MaxOldLogs = 10

if sys.platform == "darwin":
    tcllibDir = os.path.join(os.path.dirname(__file__), "tcllib")
    if os.path.isdir(tcllibDir):
        os.environ["TCLLIBPATH"] = tcllibDir

# Open a new log file and purge excess old log files
# If cannot open new log file then use default stderr.
errLog = None
try:
    import RO.OS
    docsDir = RO.OS.getDocsDir()
    if not docsDir:
        raise RuntimeError("Could not find your documents directory")

    # create new log file        
    dateStr = time.strftime("%Y-%m-%d:%H:%M:%S", time.gmtime())
    logName = "%s%s%s" % (LogPrefix, dateStr, LogSuffix)
    logPath = os.path.join(docsDir, logName)
    errLog = file(logPath, "w", 1) # bufsize=1 means line buffered

    # purge excess old log files
    oldLogGlobStr = os.path.join(docsDir, "%s????-??-??:??:??:??%s" % (LogPrefix, LogSuffix))
    oldLogPaths = glob.glob(oldLogGlobStr)
    if len(oldLogPaths) > MaxOldLogs:
        oldLogPaths = list(reversed(sorted(oldLogPaths)))
        for oldLogPath in oldLogPaths[MaxOldLogs:]:
            try:
                os.remove(oldLogPath)
            except Exception, e:
                errLog.write("Could not delete old log file %r: %s\n" % (oldLogPath, e))

except OSError, e:
    sys.stderr.write("Warning: could not open log file so using stderr\nError=%s\n" % (e,))

try:
    if errLog:
        sys.stderr = errLog
        import time
        import TUI.Version
        startTimeStr = time.strftime("%Y-%m-%dT%H:%M:%S")
        errLog.write("TUI %s started %s\n" % (TUI.Version.VersionStr, startTimeStr))
    
    import TUI.Main
    TUI.Main.runTUI()
except (SystemExit, KeyboardInterrupt):
    pass
except Exception, e:
    traceback.print_exc(file=sys.stderr)

if errLog:
    errLog.close()
