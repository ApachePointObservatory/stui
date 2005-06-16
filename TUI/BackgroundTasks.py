#!/usr/local/bin/python
"""
Handle background (invisible) tasks for the telescope UI

To do: put up a log window so the intentional error in the test case can be seen

History:
2003-02-27 ROwen	Error messages now go to the log, not stderr.
2003-03-05 ROwen	Modified to use simplified KeyVariables.
2003-05-08 ROwen	Modified to use RO.CnvUtil.
2003-06-18 ROwen	Modified to test for StandardError instead of Exception
2003-06-25 ROwen	Modified to handle message data as a dict
2004-02-05 ROwen	Modified to use improved KeyDispatcher.logMsg.
2005-06-08 ROwen	Changed BackgroundKwds to a new style class.
2005-06-16 ROwen	Modified to use improved KeyDispatcher.logMsg.
"""
import sys
import RO.CnvUtil
import RO.Constants
import RO.PhysConst
import RO.Astro.Tm
import RO.KeyVariable

class BackgroundKwds(object):
	"""Processes various keywords that are handled in the background"""
	def __init__(self,
		dispatcher = None,
		initialUTCMinusTAI = None, # UTC-TAI in seconds; the defualt is to use RO.Astro's "reasonable" initial value
		maxTimeErr = 10.0,  # max clock error (sec) before a warning is printed
	):
		self.dispatcher = dispatcher

		if initialUTCMinusTAI != None:
			RO.Astro.Tm.setUTCMinusTAI(initialUTCMinusTAI)
		
		self.maxTimeErr = maxTimeErr

		self.utcMinTAIVar = RO.KeyVariable.KeyVar(
			actor = "tcc",
			keyword="UTC_TAI",
			converters=RO.CnvUtil.asFloatOrNone,
			description="UTC time - TAI time (sec)",
			refreshCmd="show time",
			dispatcher = dispatcher,
		)
		self.utcMinTAIVar.addCallback(self.setUTCMinusTAI)
		
		self.TAIVar = RO.KeyVariable.KeyVar(
			actor = "tcc",
			keyword="TAI",
			converters=RO.CnvUtil.asFloatOrNone,
			description="Current TAI time (sec)",
			refreshCmd="show time",
			dispatcher = dispatcher,
		)
		self.TAIVar.addCallback(self.checkTAI)
		
	def setUTCMinusTAI(self, valueList, isCurrent=1, keyVar=None):
		"""Updates azimuth, altitude, zenith distance and airmass
		valueList values are: az, alt, rot
		"""
		if isCurrent and valueList[0] != None:
			RO.Astro.Tm.setUTCMinusTAI(valueList[0])

	def checkTAI(self, valueList, isCurrent=1, keyVar=None):
		"""Updates azimuth, altitude, zenith distance and airmass
		valueList values are: az, alt, rot
		"""
		if isCurrent:
			try:
				if valueList[0] != None:
					timeErr = (RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay) - valueList[0]
					
					if abs(timeErr) > self.maxTimeErr:
						self.dispatcher.logMsg(
							"Your clock appears to be off; time error = %.1f" % (timeErr,),
							severity = RO.Constants.sevWarning,
						)
			except StandardError, e:
				self.dispatcher.logMsg(
					"TAI seen but time not checked; error=%s" % (e,),
					severity = RO.Constants.sevError,
				)


if __name__ == "__main__":
	import TUI.TUIModel
	import RO.Wdg
	root = RO.Wdg.PythonTk()
		
	kd = TUI.TUIModel.getModel(True).dispatcher

	bkgnd = BackgroundKwds(dispatcher=kd)

	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":"}
	
	print "Setting TAI and UTC_TAI correctly; this should work silently."
	dataDict = {
		"TAI": (RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay,),
		"UTC_TAI": (-32,), # a reasonable value
	}
	msgDict["data"] = dataDict

	kd.dispatch(msgDict)
	
	# now generate an intentional error
	print "Setting TAI incorrectly; this would log an error if we had a log window up:"
	dataDict = {
		"TAI": ((RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay) + 999.0,),
	}
	msgDict["data"] = dataDict

	kd.dispatch(msgDict)

	root.mainloop()
