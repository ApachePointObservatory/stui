"""This file makes the TUI help directory into a package
so that TUI can find the .html files contained therein.

History:
2003-03-21 ROwen	Fixed getBaseURL to be cross-platform
"""

import os.path
import urlparse
import RO.OS

def getBaseURL():
	# convert the base path to this module
	# from native notation to URL notation (slash-separated)
	basePath = os.path.abspath(__path__[0])
	pathList = RO.OS.splitPath(basePath)
	# we expect an absolute path; in unix land this means
	# the first element will be "/"
	# but we don't want the result to start with // so...
	if pathList[0] == "/":
		pathList[0] = ""
	urlStylePath = "/".join(pathList)
	if not urlStylePath.endswith("/"):
		urlStylePath += "/"
	return urlparse.urljoin("file:", urlStylePath)
