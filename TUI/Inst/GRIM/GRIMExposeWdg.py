#!/usr/local/bin/python
"""Exposure widget.

A special subclass is required because the allowed commands change
depending on whether GRIM is in dark mode or not.

History:
2003-08-06 ROwen
2003-11-04 ROwen	bug fix: inst name is GRIM, not grim, to match
					window names and so make Config... button work
"""
import GRIMModel
from TUI.Inst.ExposeWdg import ExposeWdg

class GRIMExposeWdg(ExposeWdg):
	def __init__(self, master):
		ExposeWdg.__init__(self, master, "GRIM")

		typeWdgSet = self.expInputWdg.typeWdgSet.getWdgSet()
		self.darkTypeWdg = typeWdgSet[2]
		self.expTypeWdgSet = typeWdgSet[0:2]

		self.grimModel = GRIMModel.getModel()
		self.grimModel.modeName.addIndexedCallback(self._updMode)
		
		self._setDark(False)
	
	def _updMode(self, modeName, isCurrent=True, **kargs):
		if not isCurrent:
			return
		self._setDark(modeName == "Dark")
	
	def _setDark(self, isDark):
		if isDark:
			for wdg in self.expTypeWdgSet:
				wdg["state"] = "disabled"
			self.darkTypeWdg["state"] = "normal"
			self.darkTypeWdg.select()
		else:
			if self.darkTypeWdg["state"] != "disabled":
				# switching out of Dark mode; select Object mode
				self.expTypeWdgSet[0].select()
			for wdg in self.expTypeWdgSet:
				wdg["state"] = "normal"
			self.darkTypeWdg["state"] = "disabled"


if __name__ == '__main__':
	import Tkinter
	import RO.Wdg

	root = RO.Wdg.PythonTk()
	root.resizable(width=False, height=False)

	import TUI.Inst.ExposeTestData as ExposeTestData

	testFrame = GRIMExposeWdg(root)
	testFrame.pack(side="top", expand="yes")
	
	def setMode(wdg):
		if wdg.getBool():
			modeName = "Dark"
		else:
			modeName = "Image"
		testFrame._updMode(modeName)

	bf = Tkinter.Frame(root)
	Tkinter.Button(bf, text="Demo", command=ExposeTestData.animate).pack(side="left")
	RO.Wdg.Checkbutton(bf, text="Dark Mode", callFunc=setMode).pack(side="left")
	bf.pack(side="top")

	ExposeTestData.dispatch()

	root.mainloop()
