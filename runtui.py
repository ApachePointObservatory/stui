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
"""
import TUI.Main
TUI.Main.runTUI()
