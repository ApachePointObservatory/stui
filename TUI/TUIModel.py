#!/usr/local/bin/python
"""An object that models the overall state of TUI.
Includes the following items:
- dispatcher: the keyword dispatcher (RO.KeyDispatcher.KeyDispatcher)
	note: the network connection is dispatcher.connection
- prefs: the application preferences (TUI.TUIPrefs.TUIPrefs)
- tlSet: the set of toplevels (windows) (RO.Wdg.ToplevelSet)
- root: the root application window (Tkinter.Toplevel);
	mostly used when one to execute some Tkinter command
	(all of which require an arbitrary Tkinter object)

Note: the model must be created after the Tkinter root
has been created. Otherwise you will get a Tkinter error.

Most items are defined and loaded when the model is created.
However, "tlSet" is empty to start; use this object to add
windows to the application (so their geometry is recorded).

History:
2003-06-09 ROwen
2003-07-18 ROwen	Added getConnection, getUsername, getProgID.
2003-10-06 ROwen	Added getCmdr; changed getProgramName to getProgID
					and made it return in the case used by the Hub.
2003-10-10 ROwen	Modified to use new RO.Comm.HubConnection
2004-02-03 ROwen	Modified to use RO.OS.getPrefsDir and thus to
					look for the geom file where it really belongs.
2004-08-11 ROwen	Modified to use RO.Constants.
2004-09-03 ROwen	Modified for RO.Wdg._setHelpURLBase -> RO.Constants._setHelpURLBase.
2004-09-08 ROwen	Added logMsg method.
2005-01-05 ROwen	Changed logMsg state -> severity.
					Bug fix: logMsg was misusing severity (formerly state).
2005-06-16 ROwen	Modified logMsg for updated KeyDispatcher.logMsg.
2005-08-02 ROwen	Modified to find the help directory without it being a package.
2005-09-28 ROwen	Modified to use RO.OS.getPrefsDirs instead of getPrefsDir.
2005-10-06 ROwen	getprefsDir needs new inclNone=True argument.
2006-03-30 ROwen	Supply platform info during login.
"""
import os
import platform
import sys
import traceback
import RO.Comm
import RO.Comm.HubConnection
import RO.Constants
import RO.KeyDispatcher
import RO.OS
import RO.TkUtil
import RO.Wdg
import Tkinter
import TUI.TUIPrefs
from TUI.Version import VersionDate, VersionName

_theModel = None

def _getGeomFile():
	geomDir = RO.OS.getPrefsDirs(inclNone=True)[0]
	if geomDir == None:
		raise RuntimeError("Cannot determine prefs dir")
	geomName = RO.OS.getPrefsPrefix() + "TUIGeom"
	return os.path.join(geomDir, geomName)

def getModel(testMode = False):
	"""Obtains the model (and creates it if not already created).
	
	test mode is used for local tests of widgets.
	"""
	global _theModel
	if _theModel ==  None:
		_theModel = _Model(testMode)
	elif testMode:
		print "Warning: test mode requested but model already exists"
	return _theModel

class _Model (object):
	def __init__(self, testMode = False):
		self.root = Tkinter.Frame().winfo_toplevel()
	
		# network connection
		if testMode:
			print "Running in test mode, no real connection possible"
			connection = RO.Comm.HubConnection.NullConnection()
		else:
			connection = RO.Comm.HubConnection.HubConnection(
				loginExtra = getLoginExtra(),
			)

		# keyword dispatcher
		self.dispatcher = RO.KeyDispatcher.KeyDispatcher(
			tkWdg = self.root,
			connection = connection,
		)
	
		# TUI preferences
		self.prefs = prefs = TUI.TUIPrefs.TUIPrefs()
		
		# TUI window (topLevel) set;
		# this starts out empty; others add windows to it
		self.tlSet = RO.Wdg.ToplevelSet(
			fileName = _getGeomFile(),
			createFile = True,	# create file if it doesn't exist
		)

		# set up standard bindings (since the defaults are poor)
		RO.Wdg.stdBindings(self.root)

		# set up the base URL for TUI help
		RO.Constants._setHelpURLBase (getBaseHelpURL())
		
	def getConnection(self):
		"""Return the network connection, an RO.Comm.HubConnection object.
		"""
		return self.dispatcher.connection

	def getCmdr(self):
		"""Return the commander (in the form program.username)
		assigned by the Hub, or None if not connected.
		"""
		return self.getConnection().getCmdr()
	
	def getProgID(self):
		"""Return the program ID (in the case the hub uses),
		or None if not connected.
		"""
		return self.getConnection().getProgID()

	def getUsername(self):
		"""Return the user name assigned by the Hub,
		or None if not connected.
		"""
		return self.getConnection().getUsername()
	
	def logMsg(self,
		msgStr,
		severity = RO.Constants.sevNormal,
		copyStdErr = False,
		doTraceback = False,
	):
		"""Writes a message to the log window, if available,
		else to standard error.
		
		Inputs:
		- msgStr	message to display; a final \n is appended
		- severity		one of RO.Constants.sevNormal, sevWarning or sevError
		- copyStdErr	write copy to standard error?
		- doTraceback	write traceback to standard error?
						(if True then a copy of msgStr is always written to std error)
		"""
		self.dispatcher.logMsg(msgStr, severity = severity)
		
		if copyStdErr or doTraceback:
			sys.stderr.write (msgStr + "\n")
			if doTraceback:
				traceback.print_exc(file=sys.stderr)

def getBaseHelpURL():
	"""Return the file URL to the base directory for help"""
	# set up the base URL for TUI help
	helpDir = RO.OS.getResourceDir(TUI, "Help")
	pathList = RO.OS.splitPath(helpDir)
	if pathList[0] == "/":
		pathList = pathList[1:]
	urlStylePath = "/".join(pathList)
	if not urlStylePath.endswith("/"):
		urlStylePath += "/"
	return "file:///" + urlStylePath

def getLoginExtra():
	"""Return extra login data"""
	versName, versDate = TUI.Version.VersionStr.split()
	versData = " ".join((VersionDate, VersionName))
	platData = platform.platform()
# the following code fails on intel Macs
# at least with python 2.4.2;
# apparently gestalt is not yet working
#	if platData.lower().startswith("darwin"):
#		# replace Version-kernel#- with MacOSX-vers#-
#		macVers = platform.mac_ver()[0]
#		if macVers:
#			extraInfo = platData.split("-", 2)[-1]
#			platData = "MacOSX-%s-%s" % (macVers, extraInfo)
	wsysData = RO.TkUtil.getWindowingSystem()
	platData = " ".join((platData, wsysData))
	
	return "type=TUI version=%r platform=%r" % \
		(versData, platData)
	

if __name__ == "__main__":
	tuiModel = getModel()
	print "getBaseHelpURL = ", getBaseHelpURL()