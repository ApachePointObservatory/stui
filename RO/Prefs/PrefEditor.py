#!/usr/local/bin/python
"""Widgets for editing individual preference variables.

To Do:
- Consider modifying the font editor so the label's font changes as well as the menu
	(this may help MacOS X aqua Tk 8.4.1, which doesn't allow the menu font to vary)
  Better yet, create a Font picker dialog that shows some sample text in the chosen font
  and would allow one to immediately apply the font change (when user clicks OK in the dialog).

History:
2002-02-06 ROwen	Strings, floats and ints work; colors started, fonts not started.
2002-02-07 ROwen	Added code to sense unapplied changes
2002-02-08 ROwen	Implemented the color editor and fixed the test code
					Font editor partially implemented. Restoring default and current values fails
					and styles are not yet implemented.
2002-03-01 ROwen	Greatly simplified the display be replacing the buttons with a menu.
					Added a "changedWdg" indicator. Finished color and made great strides in font handling.
2002-03-08 ROwen	Finished the font editor.
2002-08-08 ROwen	Improved placement of editor widgets. Sorts the list of fonts.
2002-11-06 ROwen	Filter out font names with non-ascii characters, to work around a bug in aqua Tk 8.4.1;
					fixed a bug in the test code (string3 had one invalid value in validValues)
2003-03-28 ROwen	Minor code changes.
2003-04-09 ROwen	Stopped showing the range .
2003-04-09 ROwen	Changed shortDescr to helpText, preperatory to full help implementation.
2003-04-18 ROwen	Changed pop-up menu for each item to a contextual menu.
2003-04-29 ROwen	Fixes for Python 2.3:
					- fontOK broke because the test throws a different error in Python 2.3b1 than in 2.2
					- overhauled FontPrefEditor._getEditWdg to use BooleanVar and IntVar
					where appropriate, thus fixing the test for current = initial value.
2003-05-01 ROwen	Removed some debug print statements accidentally left in.
2003-08-07 ROwen	Modified PrefEditor to send the ctx config function to getEditWdg;
					bug fix: initial value not shown (default was shown instead).
2003-08-11 ROwen	Eliminated useless PrefEditFactory class and changed its method
					getEditor to global function getPrefEditor;
					modified to assume edit widgets come pre-set to the current value.
2003-09-22 ROwen	Modified to use updated PrefVar.
2003-11-17 ROwen	Modified PrefEditor to not do partial value checking;
					the edit widgets do it themselves, so it's redundant.
2004-03-05 ROwen	Modified font pref editor to support non-ascii font names.
2004-05-18 ROwen	Modified _configCtxMenu to always explicitly return a value.
					Modified for updated RO.Wdg.CtxMenu.
2004-09-20 ROwen	Bug fix: changed indicator not shown for any prefs except fonts.
2004-09-22 ROwen	Added the _ColorButton class to work around a tk bug that caused
					menubutton text to change color on aqua tk whenever the color picker was used.
2004-10-01 ROwen	Bug fix: _ColorButton used padx, pady in Frame instead of pack
					making it incompatible with older versions of Tk.
2005-06-08 ROwen	Changed PrefEditor to a new-style class.
"""
import sys
import PrefVar
import Tkinter
import tkColorChooser
import tkFont
import RO.Alg
import RO.Wdg

def getPrefEditor(
	prefVar,
	master,
	row = 0,
	column = 0,
):
	"""Returns a PrefEditor suitable for the specified PrefVar"""
	# put special cases first
	if isinstance(prefVar, PrefVar.ColorPrefVar):
		return ColorPrefEditor(prefVar, master, row, column)
	elif isinstance(prefVar, PrefVar.FontPrefVar):
		return FontPrefEditor(prefVar, master, row, column)
	elif isinstance(prefVar, PrefVar.PrefVar):
		return PrefEditor(prefVar, master, row, column)
	else:
		raise ValueError, "prefVar is of unknown type"

class PrefEditor(object):
	"""Basic preferences editor. Works for string, numeric and boolean data
	(PrefVar, StrPrefVar, IntPrefVar, FloatPrefVar, BoolPrefVar).
	"""
	def __init__(self,
		prefVar,
		master,
		row = 0,
		column = 0,
	):
		self.master = master
		self.prefVar = prefVar

		# create and set a variable to contain the edited value
		self.editVar = Tkinter.StringVar()
		self.editVar.set(self.prefVar.getValueStr())
		
		# save initial value, in case we have to restore it
		self.initialValue = self.getCurrentValue()
		
		# save last good value, for use if a typed char is rejected
		self.mostRecentValidValue = self.editVar.get()
		
		# a list (in grid order) of (widget name, sticky setting)
		wdgInfo = (
			("labelWdg", "e"),
			("changedWdg", ""),
			("editWdg", "w"),
			("unitsWdg", "w"),
		)
		self.labelWdg = Tkinter.Label(self.master, text = self.prefVar.name)
		self._addCtxMenu(self.labelWdg)
		
		self.changedVar = Tkinter.StringVar()
		self.changedWdg = Tkinter.Label(self.master, width=1, textvariable=self.changedVar)
		self._addCtxMenu(self.changedWdg)

		self.editWdg = self._getEditWdg()
		# self.rangeWdg = self._getRangeWdg()

		if self.prefVar.units:
			self.unitsWdg = Tkinter.Label(self.master, text = self.prefVar.name)
			self._addCtxMenu(self.unitsWdg)
		else:
			self.unitsWdg = None

		# grid the widgets
		for wdgName, sticky in wdgInfo:
			wdg = getattr(self, wdgName)
			if wdg:
				wdg.grid(row=row, column=column, sticky=sticky)
			column += 1
		
		self._setupCallbacks()
		
	def getCurrentValue(self):
		"""Returns the current value of the preference variable
		(not necessarily the value shown in the value editor).
		"""
		return self.prefVar.getValueStr()

	def getDefValue(self):
		"""Returns the current value of the preference variable
		(not necessarily the value shown in the value editor).
		"""
		return self.prefVar.getDefValueStr()

	def getEditValue(self):
		"""Returns the value from the editor widget"""
		return self.editVar.get()
	
	def getInitialValue(self):
		return self.initialValue
	
	def setVariable(self):
		"""Sets the preference variable to the edit value"""
		self.prefVar.setValue(self.getEditValue())
		self.updateChanged()
		
	def showValue(self, value):
		self.editVar.set(value)
		self.updateEditor()
	
	def showCurrentValue(self):
		self.showValue(self.getCurrentValue())
	
	def showDefaultValue(self):
		self.showValue(self.getDefValue())
	
	def showInitialValue(self):
		self.showValue(self.getInitialValue())
	
	def unappliedChanges(self):
		"""Returns true if the user has changed the value and it has not been applied"""
		return self.getEditValue() != self.prefVar.getValueStr()
	
	def updateEditor(self):
		"""Called after editVal is changed (and verified)"""
		pass

	def updateChanged(self):
		"""Updates the "value changed" indicator.
		"""
		self.afterID = None
		editValue = self.getEditValue()
#		print "updateChanged called"
#		print "editValue = %r" % editValue
#		print "currentValue = %r" % self.getCurrentValue()
#		print "initialValue = %r" % self.getInitialValue()
#		print "defaultValue = %r" % self.getDefValue()
		if editValue == self.getCurrentValue():
			self.changedVar.set("")
		else:
			self.changedVar.set("!")

	def _addCtxMenu(self, wdg):
		"""Convenience function; adds the usual contextual menu to a widget"""
		RO.Wdg.addCtxMenu (
			wdg = wdg,
			helpURL = self.prefVar.helpURL,
			configFunc = self._configCtxMenu,
		)
		wdg.helpText = self.prefVar.helpText
	
	def _editCallback(self, *args):
		"""Called whenever the edited value changes.
		Uses after to avoid the problem of the user entering
		an invalid character that is immediately rejected;
		that rejection doesn't show up in editVar.get
		and so the changed indicator falsely turns on.
		"""
#		print "_editCallback; afterID=", self.afterID
		if self.afterID:
			self.editWdg.after_cancel(self.afterID)
		self.afterID = self.editWdg.after(10, self.updateChanged)		
		
	def _setupCallbacks(self):
		"""Set up a callback to call self.updateChanged
		whenever the edit value changes.
		"""
		self.afterID = None
		self.editVar.trace_variable("w", self._editCallback)

	def _getEditWdg(self):
		if self.prefVar.validValues:
			# use a pop-up list of values
			# first generate a list of strings representing the values
			valueList = [self.prefVar.asStr(val) for val in self.prefVar.validValues]
			# now return a menu containing those values
			wdg = RO.Wdg.OptionMenu(
				master = self.master,
				var= self.editVar,
				items = valueList,
				helpText = self.prefVar.helpText,
				helpURL = self.prefVar.helpURL,
			)
			wdg.ctxSetConfigFunc(self._configCtxMenu)
			wdg.set(self.getInitialValue())
		else:
			wdg = self.prefVar.getEditWdg(self.master, self.editVar, self._configCtxMenu)
		return wdg

	def _getRangeWdg(self):
		return Tkinter.Label(self.master, text = self.prefVar.getRangeStr())
	
	def _getShowMenu(self):
		mbut = Tkinter.Menubutton(self.master,
			indicatoron=1,
			direction="below",
			borderwidth=2,
			relief="raised",
			highlightthickness=2,
		)
		mnu = Tkinter.Menu(mbut, tearoff=0)
		mnu.add_command(label="Current", command=self.showCurrentValue)
		mnu.add_command(label="Initial", command=self.showInitialValue)
		mnu.add_command(label="Default", command=self.showDefaultValue)
		mnu.add_separator()
		mnu.add_command(label="Apply", command=self.setVariable)
		mbut["menu"] = mnu
		return mbut

	def _configCtxMenu(self, mnu):
		def summaryFromVal(val):
			try:
				return self.prefVar.asSummary(val)
			except StandardError, e:
				sys.stderr.write("could not get summary of %r for %s: %s\n" % (val, self.prefVar.name, e))
				return "???"
		
		# basic current/initial/default menu items
		mnu.add_command(label="Current (%s)" % (summaryFromVal(self.getCurrentValue()),), command=self.showCurrentValue)
		mnu.add_command(label="Initial (%s)" % (summaryFromVal(self.getInitialValue()),), command=self.showInitialValue)
		mnu.add_command(label="Default (%s)" % (summaryFromVal(self.getDefValue()),), command=self.showDefaultValue)
		mnu.add_separator()

		# minimum and maximum values, if present
		try:
			didAdd = False
			if self.prefVar.minValue != None:
				mnu.add_command(label="Minimum (%s)" % (summaryFromVal(self.prefVar.minValue),), command=self.showCurrentValue)
				didAdd = True
			if self.prefVar.maxValue != None:
				mnu.add_command(label="Maximum (%s)" % (summaryFromVal(self.prefVar.maxValue),), command=self.showCurrentValue)
				didAdd = True
			if didAdd:
				mnu.add_separator()
		except AttributeError:
			pass
		
		# apply menu item		
		mnu.add_command(label="Apply", command=self.setVariable)
		if self.prefVar.helpURL:
			mnu.add_separator()
			return True
		return False


class _ColorButton(Tkinter.Frame, RO.Wdg.CtxMenuMixin):
	"""A button whose color can be set (without fussing
	with bitmaps and such).
	
	Note that it consists of an outer frame that does nothing
	and an inner frame that has bindings and looks like a button.
	This allows padding around the button.
	"""
	def __init__(self,
		master,
		color,
		command = None,
		height = 24,
		width = 24,
		padx = 2,
		pady = 2,
		borderwidth = 2,
		helpText = None,
		helpURL = None,
		ctxConfigFunc = None,
	):
		self.command = command
		self.helpText = helpText
		
		# self is outer frame; button is a frame within (to allow padding)
		Tkinter.Frame.__init__(self,
			master,
			borderwidth = 0,
		)
		
		self.button = Tkinter.Frame(
			self,
			background = color,
			relief = "raised",
			borderwidth = borderwidth,
			height = height,
			width = width,
		)
		self.button.pack(padx = padx, pady = pady)

		RO.Wdg.CtxMenuMixin.__init__(self,
			helpURL = helpURL,
			configFunc = ctxConfigFunc,
		)
		
		self.button.bind("<Button-1>", self._mouseDown)
		self.button.bind("<Leave>", self._leave)
		self.button.bind("<ButtonRelease>", self._buttonRelease)

	def _mouseDown(self, evt=None):
		self.button["relief"] = "sunken"
	
	def _leave(self, evt=None):
		self.button["relief"] = "raised"
	
	def _buttonRelease(self, evt=None):
		if self.button["relief"] == "sunken" and self.command:
			self.command()
		self.button["relief"] = "raised"
	
	def setColor(self, color):
		self.button["background"] = color


class ColorPrefEditor(PrefEditor):
	"""An editor for colors.
	self.editVar contains Tk strings that describe colors, e.g. "#FFFFFF"
	"""
	def _getEditWdg(self):
		wdg = _ColorButton(
			master = self.master,
			color = self.getEditValue(),
			command = self.editColor,
			helpText = self.prefVar.helpText,
			helpURL = self.prefVar.helpURL,
			ctxConfigFunc = self._configCtxMenu,
		)
		return wdg
	
	def updateEditor(self):
		"""Called after editVal is changed, to update the displayed value"""
		self.editWdg.setColor(self.getEditValue())

	def editColor(self, evt=None):
		"""Called when the color editor button is pressed"""
		oldColor = self.getEditValue()
		newColor = tkColorChooser.askcolor(oldColor)[1]
		if newColor:
			self.showValue(newColor)


class FontPrefEditor(PrefEditor):
	"""An editor for fonts.
	getEditValue() returns a dictionary of font attributes
	such as can be used to configure a Tk Font widget.
	self.editVar is not used at all, and unlike some other pref editors,
	the value passed around is obtained from prefVar.value,
	not the string version returned by prefVar.getValue()
	"""
	def _getEditWdg(self):
		currFontDict = self.prefVar.value
		fontFamilies = list(tkFont.families())
		fontFamilies.sort()
		fontSizes = [str(x) for x in range(9, 25)]
		
		# create a Font for the font editor widgets
		self.editFont = tkFont.Font(**currFontDict)
		
		nameDefVarSet = (
			("family", "Helvetica", Tkinter.StringVar()),
			("size", 12, Tkinter.IntVar()),
			("weight", "normal", Tkinter.StringVar()),
			("slant", "roman", Tkinter.StringVar()),
			("underline", False, Tkinter.BooleanVar()),
			("overstrike", False, Tkinter.BooleanVar()),
		)
		self.varDict = {}
		for varName, varDef, var in nameDefVarSet:
			# the default value in nameDefVarSet is a last ditch default
			# in case the variable itself does not have a default value
			varDef = currFontDict.get(varName, varDef)
			var.set(varDef)
			self.varDict[varName] = var
		
		frame = Tkinter.Frame(self.master)
		fontNameWdg = RO.Wdg.OptionMenu(
			master = frame,
			var = self.varDict["family"],
			items = fontFamilies,
			helpText = self.prefVar.helpText,
			helpURL = self.prefVar.helpURL,
		)
		fontNameWdg.configure(font=self.editFont)
		fontNameWdg.ctxSetConfigFunc(self._configCtxMenu)

		fontSizeWdg = RO.Wdg.OptionMenu(
			master = frame,
			items = fontSizes,
			var = self.varDict["size"],
			helpText = self.prefVar.helpText,
			helpURL = self.prefVar.helpURL,
		)
		fontSizeWdg.configure(font=self.editFont)
		fontSizeWdg.ctxSetConfigFunc(self._configCtxMenu)

		fontOptionWdg = Tkinter.Menubutton(frame,
			indicatoron=1,
			direction="below",
			borderwidth=2,
			relief="raised",
			highlightthickness=2,
		)
		mnu = Tkinter.Menu(fontOptionWdg, tearoff=0)
		mnu.add_checkbutton(label="Bold", variable=self.varDict["weight"], onvalue="bold", offvalue="normal")
		mnu.add_checkbutton(label="Italic", variable=self.varDict["slant"], onvalue="italic", offvalue="roman")
		mnu.add_checkbutton(label="Underline", variable=self.varDict["underline"], onvalue=True, offvalue=False)
		mnu.add_checkbutton(label="Overstrike", variable=self.varDict["overstrike"], onvalue=True, offvalue=False)
		fontOptionWdg["menu"] = mnu
		RO.Wdg.addCtxMenu(fontOptionWdg,
			helpURL = self.prefVar.helpURL,
			configFunc = self._configCtxMenu,
		)
		fontOptionWdg.helpText = self.prefVar.helpText
				
		fontNameWdg.pack(side="left")
		fontSizeWdg.pack(side="left")
		fontOptionWdg.pack(side="left")

		# set up a callback for each variable
		for var in self.varDict.itervalues():
			var.trace_variable("w", self._editCallback)

		return frame
	
	def getCurrentValue(self):
		"""Returns a font description dictionary"""
		return self.prefVar.getValue()
	
	def getInitialvalue(self):
		return self.initialValue.copy()
	
	def getDefValue(self):
		"""Returns a font description dictionary"""
		return self.prefVar.getDefValue()
	
	def getEditValue(self):
		"""Returns a dictionary of font attributes,
		such as are used by PrefVar FontPrefs.
		"""
		# combine options from current value (some of which may not be editable
		# with our limited font editor) with the edit values
		retValue = self.getCurrentValue()
		editValue = {}
		for name, var in self.varDict.iteritems():
			editValue[name] = var.get()
		retValue.update(editValue)
		return retValue

	def showValue(self, valueDict):
		"""Value is a dictionary of font attributes containing fields:
		"family", "size" and ?. Unknown values are ignored.
		"""
		# set pop-up menus
		for name, val in valueDict.iteritems():
			if self.varDict.has_key(name):
				self.varDict[name].set(val)

		# now update the font used for the menu text
		self._editCallback()
	
	def _editCallback(self, *args):
		self.editFont.configure(**self.getEditValue())
		editValue = self.getEditValue()
		if editValue == self.getCurrentValue():
			self.changedVar.set("")
		else:
			self.changedVar.set("!")
		
		self.updateChanged()
		
	def _setupCallbacks(self):
		# edit callback is already set up as the widgets are created.
		pass



if __name__ == "__main__":
	from RO.Wdg.PythonTk import PythonTk
	root = PythonTk()
	
	pvList = (
		PrefVar.FontPrefVar(
			name = "font1",
			category = "fonts",
			defValue = {"family":"helvetica", "size":"12"},
			helpText = "a font",
		),
		PrefVar.FontPrefVar(
			name = "font2",
			category = "fonts",
			defValue = {"family":"times", "size":"14", "weight":"bold"},
			helpText = "another font",
		),
		PrefVar.ColorPrefVar(
			name = "color1",
			category = "colors",
			defValue = "black",
			helpText = "a color",
		),
		PrefVar.ColorPrefVar(
			name = "color2",
			category = "colors",
			defValue = "red",
			helpText = "another color",
		),
		PrefVar.StrPrefVar(
			name = "string1",
			category = "strings",
			defValue = "",
			helpText = "string with no restrictions",
		),
		PrefVar.StrPrefVar(
			name = "string2",
			category = "strings",
			defValue = "foo",
			partialPattern = r"^[a-z]*$",
			helpText = "string with format ^[a-z]*$",
		),
		PrefVar.StrPrefVar(
			name = "string3",
			category = "strings",
			defValue = "foo",
			validValues = ("foo", "bar", "baz"),
			partialPattern = r"^[a-z]*$",
			helpText = "string with format ^[a-z]*$",
		),
		PrefVar.IntPrefVar(
			name ="int1",
			category = "ints",
			defValue = 0,
			helpText = "int with no restrictions",
		),
		PrefVar.IntPrefVar(
			name = "int2",
			category = "ints",
			defValue = 45,
			maxValue = 99,
			helpText = "int with default 45 and upper limit 99",
		),
		PrefVar.IntPrefVar(
			name = "int3",
			category = "ints",
			defValue = 0,
			minValue = -75,
			helpText = "int with lower limit of -75",
		),
		PrefVar.IntPrefVar(
			name = "int4",
			category = "ints",
			defValue = 0,
			minValue = -9,
			maxValue =  9,
			helpText = "int with range of [-9, 9]",
		),
		PrefVar.FloatPrefVar(
			name = "float1",
			category = "floats",
			defValue = 0,
			helpText = "float with no restrictions",
		),
		PrefVar.FloatPrefVar(
			name = "float2",
			category = "floats",
			defValue = 0,
			maxValue = 99.99,
			helpText = "float with upper limit of 99.99",
		),
		PrefVar.FloatPrefVar(
			name = "float3",
			category = "floats",
			defValue = 0, 
			minValue = -75.50,
			helpText = "float with lower limit of -75.50",
		),
		PrefVar.FloatPrefVar(
			name = "float4",
			category = "floats",
			defValue = 0,
			minValue = -9.99,
			maxValue =  9.99,
			helpText = "float with range of [-9.99, 9.99]",
		),
	)
	
	peList = []
	row = 0
	for pv in pvList:
		peList.append(getPrefEditor(pv, root, row, column = 0))
		row += 1

	root.mainloop()
