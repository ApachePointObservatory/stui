#!/usr/local/bin/python
"""Preferences for the RO.Wdg package.

Note: call 
History:
2004-08-11 ROwen	Split out from RO.Wdg.Label to make it more readily available.
2004-09-03 ROwen	Bug fix; getWdgPrefDict was calling a nonexistent function if self.prefDict not set..
					Modified for RO.Wdg.st_... -> RO.Constants.st_...
2005-01-03 ROwen	Refactored to put most code in a class.
					Added "Active Background Color" and "Active Bad Background" to PrefDict.
					These are automatically adjusted as the non-active version is modified.
					Modified the test code to output more useful information.
2005-01-05 ROwen	Modified for RO.Wdg.Label state->severity and RO.Constants.st_... -> sev...
"""
__all__ = []

import Tkinter
import RO.Constants
import RO.Prefs.PrefVar

# use lazy evaluation to avoid accessing tk root until there is one
_wdgPrefs = None

def getWdgPrefDict():
	"""Return a dictionary of widget preferences
	as preference name: preference variable.

	Preference names are:
	- Background Color
	- Bad Background
	- Foreground Color
	- Warning Color
	- Error Color
	(the following two are automatically updated from
	the non-active versions):
	- Active Background Color
	- Active Bad Background
	"""
	global _wdgPrefs
	
	if not _wdgPrefs:
		_wdgPrefs = WdgPrefs()
	return _wdgPrefs.prefDict
	
def getSevPrefDict():
	"""Return a dictionary of state preferences:
	- RO.State.Normal: Foreground Color preference variable
	- RO.State.Warning: Warning Color preference variable
	- RO.State.Error: Error Color preference variable
	
	"""
	global _wdgPrefs
	
	if not _wdgPrefs:
		_wdgPrefs = WdgPrefs()
	return _wdgPrefs.sevPrefDict

def setWdgPrefs(wdgPrefs = None):
	"""Call if you want to specify widget preferences explicitly
	instead of using defaults.
	
	Warning: ignored once _wdgPrefs is created,
	so be sure to call setWdgPrefs before calling getWdgPrefDict
	or getSevPrefDict.
	"""
	global _wdgPrefs

	if not _wdgPrefs:
		_wdgPrefs = WdgPrefs(wdgPrefs)

class WdgPrefs:
	"""Copies or creates preferences used to display
	and automatically update preferences.
	
	Uses the following preferences from prefSet, if supplied,
	else creates them with reasonable default values:
	- Bad Background,
	- Warning Color (used as a foreground color)
	- Error Color (used as a foreground color)
	- Background Color
	- Foreground Color
	
	Creates two more preferences:
	- Active Background Color
	- Active Bad Background
	These are automatically updated as the non-active version changes.
	
	Note: activeforeground is normally the same as foreground
	(at least on MacOS X or unix) so we don't bother with
	active versions of warning and error.
	
	Two attributes of interest are:
	
	- prefDict: a dictionary containing the above-listed preferences
	as preference name: preference variable.
	
	- sevPrefDict: a dictionary containing:
	  - RO.State.Normal: Foreground Color preference variable
	  - RO.State.Warning: Warning Color preference variable
	  - RO.State.Error: Error Color preference variable


	Note: the following widget attributes should update automatically
	via the resource database, without need for preference callbacks:
	background, activebackground, foreground.
	"""
	def __init__(self, prefSet = None):
		# use a widget that has the activebackground attribute
		self._tkWdg = Tkinter.Button()
		self.prefDict = {}
		self._activeBackScale = 1.0

	#	print "WdgPrefs(prefSet=%r)" % (prefSet,)
	
		def getColorPref(prefName, defColor):
			if prefSet:
				prefVar = prefSet.getPrefVar(prefName)
				if prefVar:
					return prefVar
			return RO.Prefs.PrefVar.ColorPrefVar(name = prefName, defValue = defColor)
		
		backColor = self._tkWdg.cget("background")
		foreColor = self._tkWdg.cget("foreground")
		setupList = (
			("Background Color", backColor),
			("Bad Background", "pink"),
			("Foreground Color", foreColor),
			("Warning Color", "blue2"),
			("Error Color", "red"),
		)
	
		for prefName, defColor in setupList:
			# record old prefVar, in case we want to transfer callbacks
			self.prefDict[prefName] = getColorPref (prefName, defColor)
		
		# set state pref dict
		self.sevPrefDict = {
			RO.Constants.sevNormal:  self.prefDict["Foreground Color"],
			RO.Constants.sevWarning: self.prefDict["Warning Color"],
			RO.Constants.sevError:	 self.prefDict["Error Color"],
		}

		# add activebackground color (could do the same for activeforeground,
		# but it doesn't seem to be used).	
		activeBackColor = self._tkWdg.cget("activebackground")
		backColorVals = self._tkWdg.winfo_rgb(backColor)
		activeBackColorVals = self._tkWdg.winfo_rgb(activeBackColor)
		if backColorVals == activeBackColorVals:
			# no need for separate activeBackground preference
			self._activeBackScale == 1.0
		else:
			# pick scale based on first non-zero component
			for bval, abval in zip(backColorVals, activeBackColorVals):
				if bval > 0 and abval > 0:
					self._activeBackScale = abval / float(bval)
					break
			else:
				# no sensible scaling; just use identical pref
				self._activeBackScale = 1.0
		
	#	print "self._activeBackScale =", self._activeBackScale
	
		activeBackName = "Active Background Color"
		activeBadBackName = "Active Bad Background"
		backPref = self.prefDict["Background Color"]
		badBackPref = self.prefDict["Bad Background"]
		if self._activeBackScale == 1.0:
			# no need for a separate prefs
			self.prefDict[activeBackName] = backPref
			self.prefDict[activeBadBackName] = badBackPref
		else:
			# create separate prefs and callbacks from the normal prefs to update them
	
			# add prefs
			self.prefDict[activeBackName] = RO.Prefs.PrefVar.ColorPrefVar(name = activeBackName)
			self.prefDict[activeBadBackName] = RO.Prefs.PrefVar.ColorPrefVar(name = activeBadBackName)
			
			# add callbacks to update active prefs; add to beginning of list
			# so active pref is fully updated when the remaining non-active pref's
			# callbacks are called
			backPref._callbackList.insert(0, self._updActBackPref)
			badBackPref._callbackList.insert(0, self._updActBadBackPref)
			
			# call callbacks to set values
			self._updActBackPref(backColor)
			self._updActBadBackPref(badBackPref.getValue())
			
	def scaleColor(self, color, scale):
		"""Compute the scaled version of a color.
		output (R, G, B) = input (R, G, B) * scale, clipped to 0xFFFF
		"""
#		print "scaleColor(%r, %r)" % (color, scale)
		colorVals = self._tkWdg.winfo_rgb(color)
		scaledColorVals = [min(int(val * scale), 0xFFFF) for val in colorVals]
		scaledColor = "#%04x%04x%04x" % tuple(scaledColorVals)
#		print "scaleColor(color=%r; scale=%r); scaledColor=%r" % (color, scale, scaledColor)
		return scaledColor
	
	def _updActBackPref(self, color, *args):
		"""Background preference has been updated;
		Update the active background color preference accordingly.
		
		This color is automatically updated in widgets
		when the background color changes, so read it
		rather than computing it.
		"""
		activeBackColor = self._tkWdg.cget("activebackground")
		self.prefDict["Active Background Color"].setValue(activeBackColor)
	
	def _updActBadBackPref(self, badBackColor, *args):
		"""Bad Background preference has changed;
		update Active Bad Background accordingly.
		"""
		activeBadBackColor = self.scaleColor(badBackColor, self._activeBackScale)
		self.prefDict["Active Bad Background"].setValue(activeBadBackColor)


if __name__ == "__main__":
	setWdgPrefs()
	
	wdgPrefDict = getWdgPrefDict()
	print "wdgDict:"
	prefNames = wdgPrefDict.keys()
	prefNames.sort()
	for prefName in prefNames:
		print "  %s: %r" % (prefName, wdgPrefDict[prefName].getValue())
	print
	print "sevPrefDict:"
	sevPrefDict = getSevPrefDict()
	severities = sevPrefDict.keys()
	severities.sort()
	for severity in severities:
		print "  %s: %r" % (severity, sevPrefDict[severity].getValue())
