#!/usr/local/bin/python
"""Preferences for the RO.Wdg package.

Supplies the following preferences:
Bad Background		background color for bad values
Warning Color		foreground color for warnings
Error Color			foreground color for errors
Background Color	normal background color
Foreground Color	normal foreground color

Also defines the following constant:
_BaseHelpURL

Background color is handled as follows:
- Good (normal) background color is copied from a widget whose background is never directly
  modified; hence it tracks changes to the global application background color
- Bad background color cannot be handled in this fashion, so a preference variable is used
  and a callback is registered (that's going to be a painfully slow callback if there
  are a lot of widgets to update).

History:
2004-08-11 ROwen	Split out from RO.Wdg.Label to make it more readily available.
2004-09-03 ROwen	Bug fix; getWdgPrefDict was calling a nonexistent function if _PrefDict not set..
					Modified for RO.Wdg.st_... -> RO.Constants.st_...
"""
__all__ = []

import Tkinter
import RO.Constants
import RO.Prefs.PrefVar

# these dictionaries are used to store preferences used by ROWdgs;
# use lazy evaluation so that no attempt is made to access root until there is one
_PrefDict = {}
_StatePrefDict = {}

def setWdgPrefs(prefSet = None):
	"""Call this once before using RO.Wdg to set _PrefDict (you can call it multiple times, but there is no need).
	Uses the following preferences: "Bad Background", "Warning Color", "Error Color",
	"Background Color" and "Foreground Color". However, the latter two are assumed to update
	automatically via the resource database.
	"""
	# print "SetPrefs; prefSet=%r" % (prefSet,)
	global _PrefDict

	def getColorPref(prefSet, prefName, defColor):
		if prefSet:
			prefVar = prefSet.getPrefVar(prefName)
			if prefVar:
				return prefVar
		return RO.Prefs.PrefVar.ColorPrefVar(name = prefName, defValue = defColor)
	
	setupList = (
		("Background Color", Tkinter.Label().cget("background"), False),
		("Bad Background", "pink", True),
		("Foreground Color", Tkinter.Label().cget("foreground"), False),
		("Warning Color", "blue2", True),
		("Error Color", "red", True),
	)

	for prefName, defColor, keepCallbacks in setupList:
		# record old prefVar, in case we want to transfer callbacks
		oldPref = _PrefDict.get(prefName, None)
		
		_PrefDict[prefName] = getColorPref (prefSet, prefName, defColor)

		if keepCallbacks and oldPref:
			_PrefDict[prefName]._callbackList += oldPref._callbackList[:]

def getWdgPrefDict():
	"""Return a dictionary of widget preference names and preferences.
	"""
	global _PrefDict
	if not _PrefDict:
		setWdgPrefs()
	return _PrefDict

def getWdgStatePrefDict():
	"""Return a dictionary of state, foreground color preference
	"""
	global _StatePrefDict
	if not _StatePrefDict:
		prefDict = getWdgPrefDict()
		_StatePrefDict = {
			RO.Constants.st_Normal:  prefDict["Foreground Color"],
			RO.Constants.st_Warning: prefDict["Warning Color"],
			RO.Constants.st_Error:   prefDict["Error Color"],
		}
	return _StatePrefDict
