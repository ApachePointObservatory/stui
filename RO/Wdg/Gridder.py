#!/usr/local/bin/python
"""Tools for gridding widgets

History:
2003-03-28 ROwen
2003-03-31 ROwen	Refactored to improve flexibility and enable handling
2003-04-01 ROwen	Modified to copy helpURL to label, enable and units widgets
2003-04-14 ROwen	Added EnableGridder and ChangedGridder;
					removed enable functionality from Gridder.
2003-04-15 ROwen	Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-04-24 ROwen	Added startNewCol; mod. gridWdg so row=-1 means same column;
					replaced setNextPos with setNextRow, setDefCol;
					changed def of nextCol and added getMaxNextCol.
2003-05-06 ROwen	Moved non-basic stuff to a different file;
					added support for show/hide by category;
					changed row=-1 to not mess with the column.
2003-08-11 ROwen	Added addShowHideControl, allGridded, isAllGridded;
					created widgets are RO.Wdg.StrLabel instead of Tkinter.Label
2003-11-18 ROwen	Modified to use SeqUtil instead of MathUtil.
2004-05-18 ROwen	Removed doEnable arg from Gridder; it was ignored.
					Removed enable arg from _GridSet; it was ignored.
2004-08-11 ROwen	Renamed BaseGridSet->_BaseGridSet and GridSet->_GridSet.
					Define __all__ to restrict import.
2004-09-14 ROwen	Bug fix: addShowHideWdg and gridWdg were mis-handling cat=list.
					Stopped importing RO.Wdg to avoid circular import.
2005-06-08 ROwen	Changed Gridder to a new style class.
"""
__all__ = ['Gridder']

import Tkinter
import RO.Alg
import RO.SeqUtil
import Label

class Gridder(object):
	def __init__(self,
		master,
		row=0,
		col=0,
		sticky="e",
	):
		"""Create an object that grids a set of data widgets.
		
		Inputs:
		- master	Master widget into which to grid
		- row		Starting row
		- col		Default column
		- sticky	Default sticky setting for the data widgets
		"""
		self._master = master
		self._nextRow = row
		self._defCol = col
		self._sticky = sticky
		self._nextCol = col
		self._maxNextCol = col
		self._allGridded = False
		
		# support for showing and hiding widgets by category
		# - _showHideWdgDict keys are widgets and values are lists of categories
		# - _showHideCatDict keys are categories and values are True (show) or False (hide)
		#   only widgets for which all categories are True are shown
		# - _showHideControlDict keys are categories and values are
		#   RO.Wdg.Checkbutton controls that call _showHideWdgCallback when toggled
		self._showHideWdgDict = RO.Alg.SetDict()
		self._showHideCatDict = {}
		self._showHideControlDict = {}
	
	def addShowHideControl(self, cat, ctrl):
		"""Adds A show/hide control (RO.Wdg.Checkbuttons)
		for a given category (replacing the existing control, if any).
		If all controls are gridded, then updates the show/hide status.
		
		Inputs:
		cat: category
		ctrl: one RO.Wdg.Checkbutton control (sequence not allowed)
		doCallback: apply control (else wait until _showHideCallback called)
		
		Error Conditions:
		- Raises TypeError if any widget cannot be used
		  (in which case the call has no effect)
		"""
		# verify that the widget can be used before subscribing to it
		if not hasattr(ctrl, "addCallback"):
			raise TypeError, "widget %r does not have addCallback method" % cat
		if not hasattr(ctrl, "getBool"):
			raise TypeError, "widget %r does not have getBool method" % cat
		
		# record show/hide controls	
		self._showHideControlDict[cat] = ctrl
		for ctrl in self._showHideControlDict.itervalues():
			ctrl.addCallback(self._showHideWdgCallback)
		
		# add category, if necessary
		self._showHideCatDict.setdefault(cat, False)

		# if requested, run the callback to show/hide widgets
		if self._allGridded:
			self._showHideWdgCallback()

	def addShowHideWdg(self, cat, wdg=None):
		"""Adds one or more show/hide categories to one or more widgets.
		
		If the widget(s) already have categories, the new ones are added.
		
		Inputs:
		- cat	one or more categories
		- wdg	one or more widgets; if any widget is None then it is ignored
		"""
		# add widgets to _showHideWdgDict
		wdgSet = RO.SeqUtil.asSequence(wdg)
		for wdg in wdgSet:
			if wdg:
				self._showHideWdgDict.addList(wdg, RO.SeqUtil.asList(cat))
		
		# add category to _showHideCatDict (if not already present)
		self._showHideCatDict.setdefault(cat, False)

	def allGridded(self):
		"""Call when all controls are gridded.
		Updates show/hide state if using show/hide controls
		and makes future calls to addShowHideControl update the show/hide state.
		"""
		self._allGridded = True
		if self._showHideControlDict:
			self._showHideWdgCallback()

	def gridWdg(self,
		label = None,
		dataWdg = None,
		units = None,
		cat = None,
	**kargs):
		"""Grid a set of objects in a row,
		adding label, enable and units widgets as desired.
		
		Returns a _GridSet object that allows easy access
		to the various widgets and related information.
		Increments the row counter.
		
		Inputs:
		- label			label text, variable, widget or None or False
		- dataWdg		one or a sequence of widgets;
						each of which can be None or False
		- units			units text, variable, widget or None or False
		- cat			one or more show/hide categories;
						if specified, all widgets are added
						to the show/hide list using these categories
		- row			row in which to grid;
						-1 means the same row as last time;
						default is the next row
		- col			starting column at which to grid;
						default is the default column
		- colSpan		column span for each of the data widgets
		- sticky		sticky option for each of the data widgets
		
		Notes:
		- If a widget is None then nothing is gridded
		  (and the widget is not added to gs.wdgSet)
		  but space is left for it.
		- If a widget is False then the same thing happens
		  except that no space is left for the widget.
		- If you want an empty Label widget for label or units
		  (e.g. for later alteration) then specify a value of "".
		"""
		basicKArgs = self._basicKArgs(**kargs)
		gs = _GridSet(
			master = self._master,
			label = label,
			dataWdg = dataWdg,
			units = units,
		**basicKArgs)
		self._nextRow = gs.row + 1
		self._nextCol = gs.nextCol
		self._maxNextCol = max(gs.nextCol, self._nextCol)
		if cat != None:
			self.addShowHideWdg(cat, gs.wdgSet)
		return gs
	
	def getDefCol(self):
		"""Returns the default column for calls to gridWdg
		"""
		return self._defCol
	
	def getMaxNextCol(self):
		"""Return the column following all widgets gridded so far
		"""
		return self._maxNextCol
	
	def getNextCol(self):
		"""Returns the column following the most recently gridded widgets
		"""
		return self._nextCol
	
	def getNextRow(self):
		"""Returns the the default row for the next call to gridWdg
		(typically the row following the most recently gridded widgets).
		"""
		return self._nextRow
	
	def isAllGridded(self):
		"""Returns True if all gridded, False otherwise.
		"""
		return self._allGridded
	
	def setDefCol(self, col):
		"""Sets the default column for the next call to gridWdg.
		This also increases nextCol and maxNextCol if necessary.
		"""
		self._defCol = int(col)
		self._nextCol = max(self._defCol, self._nextCol)
		self._maxNextCol = max(self._nextCol, self._maxNextCol)	
	
	def setNextRow(self, row):
		"""Sets the next row, the default row for the next call to gridWdg.
		"""
		self._nextRow = int(row)
	
	def showHideWdg(self, **kargs):
		"""Shows and hides widgets as appropriate.
		
		Inputs: one or more category=doShow pairs:
		- cat1 = doShow1
		- cat2 = doShow2
		...
		where doShow is True for show or False for hide
		
		Any categories omitted are left in their current state.
		Only widgets for which all categories are True are shown.
		
		Errors:
		Raises KeyError if a specified category does not already exist.
		"""
		# update _showHideCatDict
		for cat, doShow in kargs.iteritems():
			# make sure the category already exists
			junk = self._showHideCatDict[cat]
			# set the category
			self._showHideCatDict[cat] = doShow
			
		# use _showHideCatDict to show or hide widgets
		for wdg, catList in self._showHideWdgDict.iteritems():
			for cat in catList:
				if not self._showHideCatDict[cat]:
					wdg.grid_remove()
					break
				wdg.grid()
	
	def startNewCol(self, row=0, col=None, spacing=0):
		"""Start a new column.
		Inputs:
		- row		starting row
		- col		new default column;
					default is one after maxNextCol
					(to leave room for a spacer)
		- spacing	desired spacing between this column and the last
		
		Error Conditions:
		- if spacing and col both specified,
		  then col must be > max next column.
		  (so there is room for the spacer column)
		"""
		self._nextRow = int(row)

		if col != None:
			newDefCol = int(col)
		else:
			newDefCol = self._maxNextCol + 1
		
		if spacing:
			spaceCol = newDefCol - 1
			if spaceCol < self._maxNextCol:
				raise ValueError, "col too small; no room for spacer column"
			Tkinter.Frame(self._master, width=spacing).grid(row=row, column=spaceCol)

		self.setDefCol(newDefCol)

	def _basicKArgs(self, **kargs):
		"""Handles the basic keyword arguments for gridWdg.
		Does not handle args that might want to be positional.
		"""
		if kargs.get("row") == -1:
			kargs["row"] = self._nextRow - 1
		else:
			kargs.setdefault("row", self._nextRow)
			kargs.setdefault("col", self._defCol)
		kargs.setdefault("sticky", self._sticky)
		return kargs

	def _showHideWdgCallback(self, wdg=None):
		"""Called if any showHide widget changes state.
		"""
		for cat, wdg in self._showHideControlDict.iteritems():
			self._showHideCatDict[cat] = wdg.getBool()

		self.showHideWdg()


class _BaseGridSet:
	def __init__ (self,
		master,
		row = 0,
		col = 0,
		helpURL = None,
	):
		"""Base class for gridding a set of widgets.
		This class does nothing by itself; you should subclass
		and call the various methods (plus add your own methods as needed)
		to do the gridding.
		
		Inputs:
		- master	Master widget into which to grid the widgets
		- row		The row in which to grid the widgets
		- col		The starting column
		  
		Attributes include:
		- wdgSet: the complete set of widgets as a sequence,
			in left-to-right order. This is only widgets;
			any absent widgets are omitted from the set
		- row: the row in which the widgets were gridded
		- begCol: the first column containing a widget or space for a widget
		- nextCol: 1 + the last column containing a widget or space for a widget
		
		Also, the various functions add these, if called:
		- labelWdg: the label widget, or None if none
		- dataWdg: the widget or set of widgets, or None if none
		- unitsWdg: the units widget, or None if none
		"""
		self.master = master
		self.row = row
		self.begCol = col
		self.nextCol = col
		self.helpURL = helpURL
		self.wdgSet = []
	
	def _gridWdg(self, wdg, sticky, colSpan=1):
		"""Grids one or more widgets,
		adding non-None widgets to self.wdgSet
		
		Each widget may be a widget or:
		- None: nothing is gridded but the column advances by colSpan
		- False: nothing is gridded and the column does not advance
		"""
		wdgSet = RO.SeqUtil.asSequence(wdg)

		for wdg in wdgSet:
			if wdg:
				wdg.grid(
					row = self.row,
					column = self.nextCol,
					sticky = sticky,
					columnspan = colSpan,
				)
				self.wdgSet.append(wdg)
			if wdg != False:		
				self.nextCol += colSpan

	def _makeWdg(self, wdgInfo):
		"""Returns a widget depending on wdgInfo:
		- None or False: returns None or False
		- a string: returns an RO.Wdg.StrVariable with text=wdgInfo
		- a Tkinter Variable: returns an RO.Wdg.StrVariable with textvariable=wdgInfo
		- a Tkinter Widget: returns wdgInfo unaltered
		"""
		if wdgInfo in (None, False):
			return wdgInfo
		elif isinstance(wdgInfo, Tkinter.Widget):
			# a widget; assume it's a Label widget of some kind
			return wdgInfo
		
		if isinstance(wdgInfo, Tkinter.Variable):
			# a Tkinter variable
			wdg = Label.StrLabel(
				master = self.master,
				textvariable = wdgInfo,
				helpURL = self.helpURL,
			)
		else:
			wdg = Label.StrLabel(
				master = self.master,
				text = wdgInfo,
			)
		return wdg
	
	def _setHelpURLFromDataWdg(self, dataWdg):
		firstWdg = RO.SeqUtil.asSequence(dataWdg)[0]

		try:
			self.helpURL = firstWdg.helpURL
		except AttributeError:
			self.helpURL = None


class _GridSet (_BaseGridSet):
	def __init__ (self,
		master,
		label = None,
		dataWdg = None,
		units = None,
		row = 0,
		col = 0,
		colSpan = 1,
		sticky = "e",
	):
		"""Grids (in order):
		- a descriptive label
		- one or more data widgets
		- a units label
		
		Inputs:
		- label			label text, variable, widget or None
		- dataWdg		one or a sequence of widgets
		- units			units text, variable, widget or None
		- row			row in which to grid
		- col			starting column at which to grid
		- colSpan		column span for each of the data widgets
		- sticky		sticky option for each of the data widgets

		Notes:
		- if label or units are None then they are not gridded
		  but everything else still goes in the appropriate column.
		  If you want an empty Label widget for label or units
		  (e.g. for later alteration) then specify a value of "".
		  
		Attributes are those from _BaseGridSet plus:
		- labelWdg: the label widget, or None if none
		- dataWdg: the widget or set of widgets
		- unitsWdg: the units widget, or None if none
		"""
		_BaseGridSet.__init__(self, master, row, col)
		self._setHelpURLFromDataWdg(dataWdg)
		
		self.labelWdg = self._makeWdg(label)
		self._gridWdg(self.labelWdg, sticky="e", colSpan=1)

		self.dataWdg = dataWdg
		self._gridWdg(self.dataWdg, sticky=sticky, colSpan=colSpan)
		
		self.unitsWdg = self._makeWdg(units)
		self._gridWdg(self.unitsWdg, sticky="w", colSpan=1)


if __name__ == "__main__":
	import PythonTk
	root = PythonTk.PythonTk()
	
	wdgFrame = Tkinter.Frame(root)
	gr = Gridder(wdgFrame)
	gr.gridWdg (
		label = "Opt 1",
		dataWdg = Tkinter.Entry(wdgFrame, width=5),
		units = "mHz",
	)
	sv = Tkinter.StringVar()
	sv.set("Option 2")
	gs = gr.gridWdg (
		label = sv,
		dataWdg = Tkinter.Entry(wdgFrame, width=5),
		units = "bars",
	)
	gr.gridWdg (
		label = Tkinter.Label(wdgFrame, text="No Units"),
		dataWdg = Tkinter.Entry(wdgFrame, width=5),
	)
	gr.gridWdg (
		label = "Blank Units",
		dataWdg = Tkinter.Entry(wdgFrame, width=5),
		units = "",
	)
	gr.gridWdg (
		label = "Pair",
		dataWdg = [Tkinter.Entry(wdgFrame, width=5) for ii in range(2)],
	)
	wdgFrame.pack()
	

	root.mainloop()
