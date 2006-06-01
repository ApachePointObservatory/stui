#!/usr/local/bin/python
"""A widget to display a scrolling log of information. Log entries
may be categorized and each category may be displayed in a different color.
Each category may be individually shown or hidden.

Sutbleties:
* The display auto-scrolls if the scrollbar is at the bottom.
* If a category is shown or hidden, the display attempts to scroll intelligently:
	* If the text area has focus, it scrolls to keep the insertion cursor in view
	* Otherwise, the usual autoscroll rule applies: if the scrollbar is at the bottom,
	  it is kept there, else it is left alone
* Search is backwards, starting from the current end of selection,
	if there is a selection, else from the end. Thus you can search	repeatedly
	to get ever older finds. However, the results can be confusing
	if there is an existing selection before you start the search.

To Do:
* Clean up interface to _ShowTagWdg; don't really want to pass in yscroll
but I don't know any other way to find out if the textWdg is scrolled to
the end -- which is needed to do a good job of maintaining scroll when
showing and hiding categories

History:
2001-11-15 ROwen	The first version with history.
2002-03-05 ROwen	Modified to use GenericCallback.
2002-03-11 ROwen	Added LogWdg.setColor and ColorPrefVar handling.
2002-05-13 ROwen	Support multiple sets of categories.
2002-08-08 ROwen	Moved to RO.Wdg.
2002-11-22 ROwen	Made it difficult or impossible to change the logged data.
2002-12-05 ROwen	Added support for URL-based help.
2002-12-20 ROwen	Removed any attempt to import RO.Wdg...., thanks to pychecker.
2003-03-11 ROwen	Changed to use OptionMenu instead of ROOptionMenu.
2003-04-15 ROwen	Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-06-18 ROwen	Bug fix: was not initially auto-scrolling if not initially displayed
					(Tk or Tkinter's changed how it reports scroll position if the
					window was never displayed);
					Modified to test for StandardError instead of Exception
2003-09-30 ROwen	Fixed to use 2003-07-09 version of OptionMenu.
2004-05-18 ROwen	Moved import sys to if __name__ ==...
2004-08-11 ROwen	Modified to use RO.Wdg.Text, for an enhanced contextual menu.
					Modified the other widgets to their RO.Wdg versions
					to make it easier to set the help URL.
					Define __all__ to restrict import.
2006-06-01 ROwen	Added helpText argument.
					Made the control frame explicit so it can be easily hidden.
"""
__all__ = ['LogWdg']

import Tkinter
import RO.Alg
import Button
import Entry
import Label
import OptionMenu
import Text

class LogWdg(Tkinter.Frame):
	def __init__(self,
		master,
		catSet=(),
		maxLines = 1000,
		helpText = None,
		helpURL = None,
		width = 80,
		height = 20,
	**kargs):
		"""
		Inputs:
		- master: master widget
		- catSet: a list of (listName, catList) pairs,
		  where catlist is a list of (category name, color-or-colorPref) tuples
		  listed in order most important to least,
		  and color-or-colorPref is either a string or a ColorPrefVar
		- maxLines: the max number of lines to display, ignoring wrapping
		- helpText: the help text for the main text widget.
		- helpURL: the URL of a help page; it may include anchors for:
		  - every listName in catSet
		  - "Find" for the Find button
		  - "LogDisplay" for the log display area
		- height: height of text area, in lines
		- width: width of text area, in characters
		- **kargs: additional keyword arguments for Frame
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)
		
		self.catSet = catSet
		self.maxLineIndex = maxLines + 1
		
		def urlWithAnchor(anchor):
			if helpURL:
				return "#".join((helpURL, anchor))
			else:
				return ""
		
		self.yscroll = Tkinter.Scrollbar (
			master = self,
			orient = "vertical",
		)
		self.text = Text.Text (
			master = self,
			yscrollcommand = self.yscroll.set,
			wrap = "word",
			width = width,
			height = height,
			readOnly = True,
			helpText = helpText,
			helpURL = urlWithAnchor("LogDisplay"),
		)
		self.yscroll.configure(command=self.text.yview)
		self.text.grid(row=1, column=0, sticky="nsew")
		self.yscroll.grid(row=1, column=1, sticky="ns")
		
		# put category lists along the top, if specified
		self.ctrlFrame = Tkinter.Frame(self)
		for catListName, catList in catSet:
			showTagWdg = _ShowTagWdg(
				master = self.ctrlFrame,
				textWdg = self.text,
				yscroll = self.yscroll,
				name = catListName,
				catList = catList,
				helpURL = urlWithAnchor(catListName),
			)
			showTagWdg.pack(side="left", anchor="w")

		self.findButton = Button.Button(
			master = self.ctrlFrame,
			text = "Find:",
			command = self.doSearch,
			helpURL = urlWithAnchor("Find"),
		)
		self.findButton.pack(side="left", anchor="w")
		self.findEntry = Entry.StrEntry(
			master = self.ctrlFrame,
			width = 15,
			helpURL = urlWithAnchor("Find")
		)
		self.findEntry.bind('<KeyPress-Return>', self.doSearch)
		self.findEntry.pack(side="left", anchor="w")
		self.findCountVar = Tkinter.IntVar()

		self.ctrlFrame.grid(row=0, column=0, columnspan=2, sticky="nw")

		self.rowconfigure(1, weight=1)
		self.columnconfigure(0, weight=1)
		
		# disable editing actions
		def killEvent(evt):
			return "break"

		self.text.bind("<<Cut>>", killEvent)
		self.text.bind("<<Paste>>", killEvent)
		self.text.bind("<<Clear>>", killEvent)
		self.text.bind("<Key>", killEvent)
	
	def addOutput(self, astr, category=None):
		"""Add a line of data to the log.
		
		Inputs:
		- astr: the string to append. If you want a newline, specify the \n yourself.
		- category: name of category or None if no category
		"""
		# set auto-scroll flag true if scrollbar is at end
		# there are two cases that indicate auto-scrolling is wanted:
		# scrollPos[1] = 1.0: scrolled to end
		# scrollPos[1] = scrollPos[0]: window has not yet been painted
		scrollPos = self.yscroll.get()
		doAutoScroll = scrollPos[1] == 1.0 or scrollPos[0] == scrollPos[1]
		if category:
			self.text.insert("end", astr, (category,))
		else:
			self.text.insert("end", astr)
		extraLines = int(float(self.text.index("end")) - self.maxLineIndex)
		if extraLines > 0:
			self.text.delete("1.0", str(extraLines) + ".0")
		if doAutoScroll:
			self.text.see("end")
	
	def clearOutput(self):
		self.text.delete("0.0", "end")
	
	def doSearch(self, evt=None):
		searchStr = self.findEntry.get()
		if not searchStr:
			self.bell()
			return
		selRange = self.text.tag_ranges("sel")
		if selRange:
			startIndex = selRange[0]
		else:
			startIndex = "end"
		startIndex = self.text.search(searchStr, startIndex,
			stopindex = "0.0",
			backwards = 1,
			nocase = 1,
			regexp = 1,
			count = self.findCountVar,
		)
		foundCount = self.findCountVar.get()
		if startIndex != "":
			# text found; change selection to it
			self.text.tag_remove("sel", "0.0", "end")
			endIndex = "%s + %s chars" % (startIndex, foundCount)
			self.text.tag_add("sel", startIndex, endIndex)
			self.text.see(startIndex)
		else:
			self.bell()


class _ShowTagWdg(Tkinter.Frame):
	def __init__(self,
		master,
		textWdg,
		yscroll,
		name,
		catList,
		helpURL = None,
	):
		Tkinter.Frame.__init__(self, master)
		self.textWdg = textWdg
		self.yscroll = yscroll
		self.name = name
		self.tagList = [catCol[0] for catCol in catList]
		
		# configure tag colors
		for catName, colorObj in catList:
			if isinstance(colorObj, str):
				self.setColor(catName, colorObj)
			elif hasattr(colorObj, "addCallback"):
				colorObj.addCallback(RO.Alg.GenericCallback(self.setColor, catName), callNow=True)
			else:
				raise ValueError, "unknown color specifier %r" % (colorObj,)
		
		# set up name label (if name supplied)
		if self.name:
			nameWdg = Label.StrLabel(
				master = self,
				text = name,
				helpURL = helpURL,
			)
			nameWdg.pack(side="left", anchor="w")
			
		# set up menu of categories
		menuList = ["None"] + self.tagList[0:-1] + ["All"]
		menuList.reverse()
		self.menu = OptionMenu.OptionMenu(self,
			items = menuList,
			defValue = "All",
			helpURL = helpURL,
			callFunc = self.doMenu
		)
		self.menu.pack(side="left", anchor="w")
	
	def doMenu(self, theMenu):
		"""Show or hide the appropriate categories, based on the menu selection
		
		Subtleties:
		- If the text widget has focus, then the display is scrolled
			to keep the insertion cursor in view.
		- Otherwise, if the scrollbar is at the end, it is kept at the end.
		"""
		# save cursor position
		if self.focus_get() == self.textWdg:
			seeIndex = "insert"
		elif self.yscroll.get()[1] == 1.0:
			seeIndex = "end"
		else:
			seeIndex = 0
			
		# show/hide categories;
		# once a category matches, hide all further instances
		menuSel = theMenu.getString()
		doHide = (menuSel == "None")
		for tag in self.tagList:
			self.textWdg.tag_configure(tag, elide=doHide)
			if tag == menuSel:
				doHide = True
		
		# scroll to show cursor
		if seeIndex:
			self.textWdg.see(seeIndex)

	def setColor(self, catName, catColor, *args):
		self.textWdg.tag_configure(catName, foreground=catColor)	


if __name__ == '__main__':
	import random
	import sys
	from PythonTk import PythonTk
	root = PythonTk()
	
	catList = (("Error","red"), ("Warning","blue2"), ("Information","black"))
	catOnlyList = map(lambda x: x[0], catList)

	testFrame = LogWdg (
		master=root,
		catSet = [("Replies:", catList)],
		maxLines=50,
	)
	testFrame.grid(row=0, column=0, sticky="nsew")
	
	entry = Tkinter.Entry(root)
	entry.grid(row=1, column=0, sticky="nsew")
	def addTolog (evt):
		try:
			astr = entry.get()
			entry.delete(0,"end")
			
			testFrame.addOutput(astr + "\n", category=random.choice(catOnlyList))
		except StandardError, e:
			sys.stderr.write ("Could not extract or send: %s\n" % (astr))
			sys.stderr.write ("Error: %s\n" % (e))

	entry.bind('<KeyPress-Return>', addTolog)

	# supply some fake data
	for ii in range(50):
		testFrame.addOutput("sample entry %s\n" % ii, category=random.choice(catOnlyList))

	root.rowconfigure(0, weight=1)
	root.columnconfigure(0, weight=1)

	root.mainloop()
