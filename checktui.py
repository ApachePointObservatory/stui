#!/usr/local/bin/python
"""Version of runtui.py that checks the code with pychecker.

Location is everything:
This script's directory is automatically added to sys.path,
so having this script in the same directory as RO and TUI
makes those packages available without setting PYTHONPATH.

History:
2004-05-18 ROwen	makes it easy to use pychecker
"""
import pychecker.checker
import TUI.Main
TUI.Main.runTUI()
