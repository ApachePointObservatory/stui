#!/usr/local/bin/python
"""
A basic widget for showing the progress being made in a task.
Includes a countdown timer RemainingTime.

History:
2002-03-15 ROwen	Added a start method to TimeBar.
2002-07-30 ROwen	Moved into the RO.Wdg module.
2002-12-20 ROwen	Changed bd to borderwidth for clarity.
2003-07-25 ROwen	ProgressbBar: added barBorder, helpText, helpURL;
					can now be resized while in use;
					fixed bugs affecting large and small borderwidths.
					TimeBar: renamed from TimeRemaining; added countUp and updateInterval;
					improved accuracy of pause and resume
2004-05-18 ROwen	Changed ProgressBar.configure to ._configureEvt to avoid collision
					with Tkinter.Frame.configure.
2004-08-11 ROwen	Fixed some import errors.
					Define __all__ to restrict import.
2004-09-14 ROwen	Modified test code to not import RO.Wdg.
2005-08-03 ROwen	Modified to handle max=min gracefully instead of raising an exception.
					Added doc strings to many methods.
2006-03-06 ROwen	Added setUnknown method. To support this, many parameters
					now can take two values for (known, unknown) state.
"""
__all__ = ['ProgressBar', 'TimeBar']

import time
import RO.SeqUtil
import Tkinter
import Button
import Entry
import Gridder
import Label

class ProgressBar (Tkinter.Frame):
	"""A bar graph showing a value or fraction of a task performed.
	
	Contains three widgets:
	- labelWdg: an optional label (None if absent)
	- cnv: the bar graph
	- numWdg: an optional numerical value display
	
	Inputs:
	- minValue: value for zero-length bar
	- maxValue: value for full-length bar
	- value: starting value
	- label: one of: a string, Tkinter Variable, Tkinter widget or None
	- constrainValue: if value is out of range, pin it else display as supplied
		the bar graph is always constrained, this only affects the numeric display
	- valueFormat: numeric value is displayed as valueFormat % value;
		set to None if not wanted.
		If two values, the 2nd is the string displayed for unknown value.
	
	The following control the appearance of the progress bar
	and the background field against which it is displayed
	- barLength: length of full bar (pixels) within the background border;
	- barThick: thickness of bar (pixels) within the background border;
		if horizontal then defaults to label height, else defaults to 10
	- barFill: color of bar; if two values, the 2nd is used for unknown value.
	- barStipple: stipple pattern for bar; if two values, the 2nd is used for unknown value.
	- barBorder: thickness of black border around progress bar; typically 0 or 1;
		to the extent possible, this is hidden under the background's border
	- **kargs options for the bar's background field (a Tkinter Canvas),
	  including the following which default to Entry's default settings
	  - borderwidth: thickness of border around bar's background field
	  - relief: type of border around bar's background field
	  - background: color of bar's background field
	"""
	UnkValue = "?"
	def __init__ (self,
		master,
		minValue=0,
		maxValue=100,
		value=0,
		label = None,
		constrainValue = False,
		valueFormat=("%d", "?"),
		isHorizontal = True,
		barLength = 20,
		barThick = None,
		barFill = "dark gray",
		barStipple = (None, "gray50"),
		barBorder = 0,
		helpText = None,
		helpURL = None,
	**kargs):
		# handle defaults for background, borderwidth and relief
		e = Tkinter.Entry()
		for item in ("background", "borderwidth", "relief"):
			kargs.setdefault(item, e[item])
		
		# handle default=0 for other borders
		for item in ("selectborderwidth", "highlightthickness"):
			kargs.setdefault(item, 0)

		Tkinter.Frame.__init__(self, master)

		# basics
		self.constrainValue = constrainValue
		self.valueFormat = RO.SeqUtil.oneOrNAsList(valueFormat, 2)
		self.isHorizontal = isHorizontal
		self.knownInd = 0 # 0 for known, 1 for unknown value
		self.fullBarLength = barLength
		if barThick == None:
			if self.isHorizontal:
				self.barThick = 0
			else:
				self.barThick = 10
		else:
			self.barThick = barThick
		self.barFill = RO.SeqUtil.oneOrNAsList(barFill, 2)
		self.barStipple = RO.SeqUtil.oneOrNAsList(barStipple, 2)
		self.barBorder = barBorder
		self.hideBarCoords = (-1, -1 - self.barBorder) * 2
		self.helpText = helpText
		self.helpURL = helpURL

		cnvPadY = 0
		if self.isHorizontal:
			labelAnchor = "e"
			packSide = "left"
			if barThick == None: # default to label hieght
				cnvPadY = 5
				packFill = "both"
			else:
				packFill = "x"
			cnvWidth, cnvHeight = self.fullBarLength, self.barThick
			numAnchor = "w"
		else:
			labelAnchor = "center"
			packSide = "bottom"
			packFill = "y"
			cnvWidth, cnvHeight = self.barThick, self.fullBarLength
			numAnchor = "center"

		# handle label
		self.labelWdg = self._makeWdg(label, anchor = labelAnchor)
		if self.labelWdg != None:
			self.labelWdg.pack(side = packSide)
		
		# create canvas for bar graph
		self.cnv = Tkinter.Canvas(self,
			width = cnvWidth,
			height = cnvHeight,
		**kargs)
		self.cnv.pack(side = packSide, expand = True, fill = packFill, pady = cnvPadY)
		
		# thickness of canvas border; initialize to 0 and compute later
		# drawable width/height = winfo_width/height - (2 * border)
		self.cnvBorderWidth = 0

		# bar rectangle (starts out at off screen and zero size)
		self.barRect = self.cnv.create_rectangle(
			fill = self.barFill[self.knownInd],
			stipple = self.barStipple[self.knownInd],
			width = self.barBorder,
			*self.hideBarCoords
		)
		
		# handle numeric value display
		if self.valueFormat[0]:
			self.numWdg = Label.StrLabel(self,
				anchor = numAnchor,
				formatStr = self.valueFormat[0],
				helpText = self.helpText,
				helpURL = self.helpURL,
			)
		elif self.labelWdg == None and self.barThick == None:
			# use an empty label to force bar thickness
			def nullFormat(astr):
				return ""
			self.numWdg = Label.StrLabel(self, formatFunc = nullFormat)
		else:
			self.numWdg = None
		if self.numWdg != None:
			self.numWdg.pack(side = packSide, anchor = numAnchor)
		
		# set values and update display
		self.value = value
		self.minValue = minValue
		self.maxValue = maxValue

		self.cnv.bind('<Configure>', self._configureEvt)
		self._setSize()

	def clear(self):
		"""Hide progress bar and associated value label"""
		self.cnv.coords(self.barRect, *self.hideBarCoords)
		if self.numWdg:
			self.numWdg["text"] = ""

	def setValue(self,
		newValue,
		newMin = None,
		newMax = None,
	):
		"""Set the current value and optionally one or both limits.
		
		Note: always computes bar scale, numWdg width and calls update.
		"""
		self.knownInd = 0
		if self.constrainValue:
			newValue = max(min(newValue, self.maxValue), self.minValue)
		self.value = newValue
		self.setLimits(newMin, newMax)
	
	def setUnknown(self):
		"""Display an unknown value"""
		self.knownInd = 1
		self.value = self.maxValue
		self.fullUpdate()
	
	def setLimits(self,
		newMin = None,
		newMax = None,
	):
		"""Set one or both limits.
		
		Note: always computes bar scale, numWdg width and calls update.
		"""
		if newMin != None:
			self.minValue = newMin
		if newMax != None:
			self.maxValue = newMax
		self.fullUpdate()
	
	def fullUpdate(self):
		"""Redisplay assuming settings have changed
		(e.g. current value, limits or isKnown).
		Compute current bar scale and numWdg width and then display.
		"""
		# compute bar scale
		try:
			self.barScale = float(self.fullBarLength) / float(self.maxValue - self.minValue)
		except ArithmeticError:
			self.barScale = 0.0

		# set bar color scheme
		self.cnv.itemconfig(
			self.barRect,
			fill = self.barFill[self.knownInd],
			stipple = self.barStipple[self.knownInd],
		)

		# set width of number widget
		if self.numWdg:
			# print "valfmt=%r, knownInd=%r, minValue=%r, maxValue=%r" % (self.valueFormat, self.knownInd, self.minValue, self.maxValue)
			if self.knownInd:
				maxLen = max([len(self.valueFormat[self.knownInd] % (val,)) for val in (self.minValue, self.maxValue)])
			else:
				maxLen = len(self.valueFormat[self.knownInd])
			self.numWdg["width"] = maxLen

		self.update()

	def update(self):
		"""Redisplay based on current values."""
		# 0,0 is upper-left corner of canvas, but *includes* the border
		# thus positions must be offset
		# the smallest starting position required is 1 - self.cnvBorderWidth
		# but -1 is simpler and works for all cases
		value=self.value
		
		barLength = self._valueToLength(value)
		if barLength <= 0:
			# works around some a Tk bug or misfeature
			x0, y0, x1, y1 = self.hideBarCoords
		elif barLength >= self.fullBarLength:
			# works around a Tk bug or misfeature that is only relevant if the bar has a border
			x0 = y0 = 0
			x1 = self.cnvSize[0] - 1
			y1 = self.cnvSize[1] - 1
		elif self.isHorizontal:
			x0 = 0
			y0 = 0
			x1 = self._valueToLength(value) + self.cnvBorderWidth
			y1 = self.cnvSize[1] - 1
		else:
			x0 = 0
			y0 = (self.fullBarLength - self._valueToLength(value)) + self.cnvBorderWidth
			x1 = self.cnvSize[0] - 1
			y1 = self.cnvSize[1] - 1
		# print "x0, y0, x1, y1 =", x0, y0, x1, y1
		self.cnv.coords(self.barRect, x0, y0, x1, y1)

		# And update the label
		if self.numWdg:
			if self.knownInd == 0:
				self.numWdg["text"] = self.valueFormat[self.knownInd] % (value,)
			else:
				self.numWdg["text"] = self.valueFormat[self.knownInd]
		self.cnv.update_idletasks()

	def _configureEvt(self, evt=None):
		"""Handle the <Configure> event.
		"""
		self._setSize()
		self.update()

	def _makeWdg(self, wdgInfo, **kargs):
		"""Return a widget depending on wdgInfo:
		- None or False: returns None or False
		- a string: returns a Label with text=wdgInfo
		- a Tkinter Variable: returns a Label with textvariable=wdgInfo
		- a Tkinter Widget: returns wdgInfo unaltered
		
		kargs is ignored if wdgInfo is a widget
		"""
		if wdgInfo == None:
			return wdgInfo
		elif isinstance(wdgInfo, Tkinter.Widget):
			# a widget; assume it's a Label widget of some kind
			return wdgInfo
		
		# at this point we know we are going to create our own widget
		# set up the keyword arguments
		kargs.setdefault("helpText", self.helpText)
		kargs.setdefault("helpURL", self.helpURL)
		if isinstance(wdgInfo, Tkinter.Variable):
			kargs["textvariable"] = wdgInfo
		else:
			kargs["text"] = wdgInfo

		return Label.StrLabel(self, **kargs)

	def _setSize(self):
		"""Compute or recompute bar size and associated values."""
		# update border width
		self.cnvBorderWidth = int(self.cnv["borderwidth"]) + int(self.cnv["selectborderwidth"]) + int(self.cnv["highlightthickness"])
		self.cnvSize = [size for size in (self.cnv.winfo_width(), self.cnv.winfo_height())]
		barSize = [size - (2 * self.cnvBorderWidth) for size in self.cnvSize]
		
		# compute bar length
		if self.isHorizontal:
			self.fullBarLength = barSize[0]
		else:
			self.fullBarLength = barSize[1]
		# print "_setSize; self.fullBarLength =", self.fullBarLength
				
		# recompute scale and update bar display
		self.fullUpdate()
	
	def _valueToLength(self, value):
		"""Compute the length of the bar, in pixels, for a given value.
		This is the desired length, in pixels, of the colored portion of the bar.
		"""
		barLength = (float(value) - self.minValue) * self.barScale
		# print "barLength =", barLength
		barLength = int(barLength + 0.5)
		# print "barLength =", barLength
		return barLength


class TimeBar(ProgressBar):
	"""Progress bar to display elapsed or remaining time in seconds.
	Inputs:
	- countUp: if True, counts up, else counts down
	- autoStop: automatically stop when the limit is reached
	- updateInterval: how often to update the display (sec)
	**kargs: other arguments for ProgressBar, including:
	  - value: initial time;
	    typically 0 for a count up timer, maxValue for a countdown timer
	    if omitted then 0 is shown and the bar does not progress until you call start.
	  - minvalue: minimum time; typically 0
	  - maxValue: maximum time
	"""
	def __init__ (self,
		master,
		countUp = False,
		valueFormat = ("%3.0f sec", "? sec"),
		autoStop = False,
		updateInterval = 0.1,
	**kargs):
		ProgressBar.__init__(self,
			master = master,
			valueFormat = valueFormat,
			**kargs
		)
		self._autoStop = bool(autoStop)
		self._countUp = bool(countUp)

		self._afterID = None
		self._updateIntervalMS = int((updateInterval * 1000) + 0.5)
		self._startTime = None

		if kargs.has_key("value"):
			self.start(kargs["value"])
	
	def clear(self):
		"""Set the bar length to zero, clear the numeric time display and stop the timer.
		"""
		self._cancelUpdate()
		ProgressBar.clear(self)
		self._startTime = None
	
	def pause(self, value = None):
		"""Pause the timer.
		
		Inputs:
		- value: the value at which to pause; if omitted then the current value is used
		
		Error conditions: does nothing if not running.
		"""
		if self._cancelUpdate():
			if value:
				self.setValue(value)
			else:
				self._updateTime(reschedule = False)
	
	def resume(self):
		"""Resume the timer from the current value.

		Does nothing if not paused or running.
		"""
		if self._startTime == None:
			return
		self._startUpdate()
	
	def start(self, value = None, newMin = None, newMax = None, countUp = None):
		"""Start the timer.

		Inputs:
		- value: starting value; if None, set to 0 if counting up, max if counting down
		- newMin: minimum value; if None then the existing value is used
		- newMax: maximum value: if None then the existing value is used
		- countUp: if True/False then count up/down; if None then the existing value is used
		
		Typically you will only specify newMax or nothing.
		"""
		if newMin != None:
			self.minValue = float(newMin)
		if newMax != None:
			self.maxValue = float(newMax)
		if countUp != None:
			self._countUp = bool(countUp)

		if value != None:
			value = float(value)
		elif self._countUp:
			value = 0.0
		else:
			value = self.maxValue
		self.setValue(value)
		
		self._startUpdate()
	
	def _cancelUpdate(self):
		"""Stops next scheduled update; returns True if there was one,
		False otherwise.
		"""
		if self._afterID:
			self.after_cancel(self._afterID)
			self._afterID = ""
			return True
		else:
			return False
	
	def _startUpdate(self):
		"""Starts updating from the current value.
		"""
		if self._countUp:
			self._startTime = time.time() - self.value
		else:
			self._startTime = time.time() - (self.maxValue - self.value)
		self._updateTime()

	def _updateTime(self, reschedule = True):
		"""Automatically update the elapsed time display.
		Call once to get things going.
		"""
		# print "_updateTime called"
		# cancel pending update, if any
		self._cancelUpdate()
		
		if self._startTime == None:
			raise RuntimeError, "bug! nothing to update"
		
		# update displayed value
		if self._countUp:
			value = time.time() - self._startTime
			if (self._autoStop and value >= self.maxValue):
				self.setValue(self.maxValue)
				self._cancelUpdate()
				return
		else:
			value = (self._startTime + self.maxValue) - time.time()
			if (self._autoStop and value <= 0.0):
				self.setValue(0)
				self._cancelUpdate()
				return
		
		self.setValue(value)

		# if requested, schedule next update
		if reschedule:
			self._afterID = self.after (self._updateIntervalMS, self._updateTime)
		

if __name__ == "__main__":
	import PythonTk
	root = PythonTk.PythonTk()
	
	# horizontal and vertical progress bars

	hProg = [ProgressBar(
				root,
				isHorizontal = True,
				borderwidth = bw,
				barLength = 99,
				relief = "solid",
			) for bw in (0, 1, 2, 10)
		]
	vProg = [ProgressBar(
				root,
				isHorizontal = False,
				borderwidth = bw,
				barLength = 99,
				relief = "solid",
			) for bw in (0, 1, 2, 10)
		]

	def setProg(*args):
		for pb in hProg + vProg:
			pb.setValue (
				newValue = valEntry.getNum(),
				newMin = minEntry.getNum(),
				newMax = maxEntry.getNum(),
			)
	
	valEntry = Entry.IntEntry(root, defValue = 50, width=5, callFunc = setProg)
	minEntry = Entry.IntEntry(root, defValue =  0, width=5, callFunc = setProg)
	maxEntry = Entry.IntEntry(root, defValue = 99, width=5, callFunc = setProg)
	
	setProg()

	gr = Gridder.Gridder(root)
	
	gr.gridWdg ("Val", valEntry)
	gr.gridWdg ("Minimum", minEntry)
	gr.gridWdg ("Maximum", maxEntry)
	gr.gridWdg (False)  # spacer row


	vbarRowSpan = gr.getNextRow()
	col = gr.getNextCol()
	for vpb in vProg:
		vpb.grid(row=0, column = col, rowspan = vbarRowSpan)
		col += 1
	root.grid_rowconfigure(vbarRowSpan-1, weight=1)
	
	hbarColSpan = col + 1
	for hpb in hProg:
		gr.gridWdg(False, hpb, colSpan=hbarColSpan, sticky="")
	
	root.grid_columnconfigure(hbarColSpan-1, weight=1)
	
	# time bars

	def startRemTime():
		time = timeEntry.getNum()
		for bar in timeBars:
			bar.start(time)
			
	def pauseRemTime():
		for bar in timeBars:
			bar.pause()
	
	def resumeRemTime():
		for bar in timeBars:
			bar.resume()
	
	def clearRemTime():
		for bar in timeBars:
			bar.clear()
			

	timeEntry = Entry.IntEntry(root, defValue = 9, width=5)
	gr.gridWdg ("Rem Time", timeEntry)
	gr.gridWdg (False, (
			Button.Button(root, text="Start", command=startRemTime),
			Button.Button(root, text="Pause", command=pauseRemTime),
			Button.Button(root, text="Resume", command=resumeRemTime),
			Button.Button(root, text="Clear", command=clearRemTime),
		),
	)

	hTimeBar = [TimeBar(
			master=root,
			label = "Time:",
			isHorizontal = True,
			autoStop = countUp,
			valueFormat = "%3.1f sec",
			countUp = countUp,
		) for countUp in (False, True)
	]
	for hbar in hTimeBar:
		gr.gridWdg(False, hbar, colSpan=hbarColSpan, sticky="ew")

	vTimeBar = [TimeBar(
			master=root,
			label = "Time",
			isHorizontal = False,
			autoStop = not countUp,
			countUp = countUp,
		) for countUp in (False, True)
	]
	col = gr.getNextCol()
	for vbar in vTimeBar:
		vbar.grid(row=0, column=col, rowspan = gr.getNextRow(), sticky="ns")
		col += 1
	timeBars = hTimeBar + vTimeBar

	root.mainloop()
