#!/usr/local/bin/python
"""Tools for gridding widgets

History:
2003-05-06 ROwen	Adapted from ChangedGridder.
2004-05-18 ROwen	Modified _StatusConfigGridSet._makeChangedWdg
					to eliminate two unused args (colSpan and sticky).
2004-08-11 ROwen	Renamed StatusConfigGridSet->_StatusConfigGridSet.
					Define __all__ to restrict import.
2004-09-14 ROwen	Stopped importing RO.Wdg to avoid circular imports.
2004-11-29 ROwen	Modified to include ConfigCat as a class constant.
"""
__all__ = ['StatusConfigGridder']

import Tkinter
import RO.MathUtil
import ChangedIndicator
import Gridder

ConfigCat = "config"

class StatusConfigGridder(Gridder.Gridder):
	ConfigCat = ConfigCat
	def __init__(self,
		master,
		row=0,
		col=0,
		sticky="e",
		clearMenu="Clear",
		defMenu="Default",
	):
		"""Create an object that grids a set of status widgets
		and possibly an associated set of configuration widgets
		with a changed indicator.
		
		Inputs:
		- master	Master widget into which to grid
		- row		Starting row
		- col		Starting column
		- sticky	Default sticky setting for the
					status and config widgets
		"""
		Gridder.Gridder.__init__(self,
			master = master,
			row = row,
			col = col,
			sticky = sticky,
		)
		self.clearMenu = clearMenu
		self.defMenu = defMenu
	
	def gridWdg(self,
		label = None,
		dataWdg = None,
		units = None,
		changed = True,
		cfgWdg = None,
		cat = None,
		clearMenu = None,
		defMenu = None,
	**kargs):
		"""Grids (in order)
		- labelWdg: a label widget
		- dataWdg: one or more status widgets
		- unitsWdg: units
		(the following are all None if cfgWdg not specified):
		- changedWdg: a "setting changed" widget
		- cfgWdg: one or more config widgets
		- cfgUnitsWdg: a config units label
		
		Configuration widgets are automatically added
		to the show/hide set ConfigCat and so are hidded by default.
		To display them you must call showHideWdg(config=True)
		
		Warning: a widget cannot be gridded twice, so:
		- Units cannot be an actual widget; it must be a string
		  or variable (or None)
		- There should be no common widgets in dataWdg or cfgWdg

		Returns a _StatusConfigGridSet object that allows easy access
		to the various widgets and related information.
		Increments row.next.
		"""
		basicArgs = self._basicKArgs(**kargs)
		clearMenu = clearMenu or self.clearMenu
		defMenu = defMenu or self.defMenu
		gs = _StatusConfigGridSet(
			master = self._master,
			label = label,
			dataWdg = dataWdg,
			cfgWdg = cfgWdg,
			units = units,
			changed = changed,
			clearMenu = clearMenu,
			defMenu = defMenu,
		**basicArgs)
		self._nextRow = gs.row + 1
		self._nextCol = max(gs.nextCol, self._nextCol)

		if cat != None:
			self.addShowHideWdg(cat, gs.wdgSet)
		
		# set show/hide category ConfigCat for configuration widgets
		if cfgWdg:
			self.addShowHideWdg(ConfigCat, gs.changedWdg)
			self.addShowHideWdg(ConfigCat, gs.cfgWdg)
			self.addShowHideWdg(ConfigCat, gs.cfgUnitsWdg)

		return gs


class _StatusConfigGridSet(Gridder._BaseGridSet):
	def __init__ (self,
		master,
		label = None,
		dataWdg = None,
		units = None,
		changed = True,
		cfgWdg = None,
		cfgUnits = None,
		row = 0,
		col = 0,
		colSpan = 1,
		cfgColSpan = None,
		sticky = "e",
		cfgSticky = None,
		clearMenu = "Clear",
		defMenu = "Default",
	):
		"""Creates and grids (in order) the following attributes:
		- labelWdg: a label widget
		- dataWdg: one or more status widgets
		- unitsWdg: units
		(the following are all None if cfgWdg not specified):
		- changedWdg: a "setting changed" widget
		- cfgWdg: one or more config widgets
		- cfgUnitsWdg: a config units label
		
		Inputs:
		- label			label text, variable, widget or None
		- dataWdg		one or more status widgets
		- units			units text, variable, widget or None;
						if a widget then see Error Conditions below.
		- changed		changed indicator widget or
						True to auto-create or None for none;
						ignored if cfgWdg == None
		- cfgWdg		one or more configuration widgets
		- cfgUnits		units for the config widget;
						defaults to units;
						ignored if cfgWdg == None
		- row			row in which to grid
		- col			starting column at which to grid
		- colSpan		column span for each of the status widgets
		- cfgColSpan	column span for each of the config widgets;
						defaults to colSpan
		- sticky		sticky option for the status widgets
		- cfgSticky		sticky option for the config widgets
						defaults to sticky

		Error Conditions:
		- If you specify a widget for units and also specify cfgWdg
		  then you must specify cfgUnits (as something other
		  then the units widget) or a ValueError exception is thrown.
		  This is because a widget cannot be gridded in two places.	  

		Notes:
		- If a widget is None then nothing is gridded
		  (and the widget is not added to gs.wdgSet)
		  but space is left for it.
		- If a widget is False then the same thing happens
		  except that no space is left for the widget.
		- If you want an empty Label widget for label or units
		  (e.g. for later alteration) then specify a value of "".
		  
		Attributes are those for _BaseGridSet plus
		those listed at the start of this comment block.
		"""
		if cfgColSpan == None:
			cfgColSpan = colSpan
		if cfgUnits == None:
			cfgUnits = units
		if cfgSticky == None:
			cfgSticky = sticky

		Gridder._BaseGridSet.__init__(self, master, row, col)
		self._setHelpURLFromDataWdg(dataWdg)
		
		self.labelWdg = self._makeWdg(label)
		self._gridWdg(self.labelWdg, sticky="e", colSpan=1)

		self.dataWdg = dataWdg
		self._gridWdg(self.dataWdg, sticky=sticky, colSpan=colSpan)
		
		self.unitsWdg = self._makeWdg(units)
		self._gridWdg(self.unitsWdg, sticky="w", colSpan=1)
		
		if cfgWdg:
			self.changedWdg = self._makeChangedWdg(
				changed = changed,
				cfgWdg = cfgWdg,
				clearMenu = clearMenu,
				defMenu = defMenu,
			)
			self._gridWdg(self.changedWdg, sticky="", colSpan=1)

			self.cfgWdg = cfgWdg
			self._gridWdg(self.cfgWdg, sticky=cfgSticky, colSpan=cfgColSpan)
			
			self.cfgUnitsWdg = self._makeWdg(cfgUnits)
			if self.cfgUnitsWdg and self.cfgUnitsWdg == self.unitsWdg:
				raise ValueError, "units must not be a widget"
			self._gridWdg(self.cfgUnitsWdg, sticky="w", colSpan=1)
		else:
			self.changedWdg = None
			self.cfgWdg = None
			self.cfgUnitsWdg = None
			self.nextCol = 1 + cfgColSpan + 1

	def _makeChangedWdg(self,
		changed,
		cfgWdg,
		clearMenu = None,
		defMenu = None,
	):
		if not changed:
			return None
			
		if isinstance(changed, Tkinter.Widget):
			changedWdg = changed
			if hasattr(changedWdg, "addWdg"):
				changedWdg.addWdg(cfgWdg)
		else:
			changedWdg = ChangedIndicator.ChangedIndicator(
				master = self.master,
				wdgOrSet = cfgWdg,
				helpURL=self.helpURL,
				clearMenu = clearMenu,
				defMenu = defMenu,
			)
		return changedWdg

