"""This file makes the TUI help directory into a package
so that TUI can find the .html files contained therein.

History:
2003-03-21 ROwen	Fixed getBaseURL to be cross-platform
"""
import os.path

from PlaySounds import *

def getBasePath():
	# return the base path of this module
	return os.path.abspath(__path__[0])
