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
"""
import os
import sys
import traceback

OldLogName = "oldtuilog.txt"
LogName = "tuilog.txt"

# Try to open a new log file
# (after changing existing log to old log).
# If it fails then use default stderr.
errLog = None
try:
    import RO.OS
    docsDir = RO.OS.getDocsDir()
    if not docsDir:
        raise RuntimeError("Could not find your home directory")

    logPath = os.path.join(docsDir, LogName)
    oldLogPath = os.path.join(docsDir, OldLogName)
    if os.path.isfile(logPath):
        if os.path.isfile(oldLogPath):
            os.remove(oldLogPath)
        os.rename(logPath, oldLogPath)
    errLog = file(logPath, "w", 1) # bufsize=1 means line buffered
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
