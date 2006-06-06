#!/usr/local/bin/python
"""About TUI window

2003-12-17 ROwen
2004-03-08 ROwen	Expanded the text and made it center-justified.
					Moved the code to a separate class.
					Added test code.
2004-05-18 ROwen	Stopped obtaining TUI model in addWindow; it was ignored.
					Thus stopped importing TUI.TUIModel in the main code.
2005-10-24 ROwen	Updated the acknowledgements to include WingIDE.
2006-06-01 ROwen	Updated the acknowledgements to include Fritz Stauffer.
"""
import RO.Wdg
import TUI.Version

def addWindow(tlSet):
	tlSet.createToplevel(
		name = "TUI.About TUI",
		resizable = False,
		visible = False,
		wdgFunc = AboutWdg,
	)

class AboutWdg(RO.Wdg.StrLabel):
	def __init__(self, master):
		RO.Wdg.StrLabel.__init__(
			self,
			master = master,
			text = u"""APO 3.5m Telescope User Interface
Version %s
by Russell Owen

With special thanks to:
- Craig Loomis and Fritz Stauffer for the APO hub
- Bob Loewenstein for Remark
- Dan Long for the photograph used for the icon
- The APO observing specialists and users
  for suggestions and bug reports
- Wingware for free use of WingIDE
""" % (TUI.Version.VersionStr,),
			justify = "left",
			borderwidth = 10,
		)


if __name__ == "__main__":
	import TUI.TUIModel
	root = RO.Wdg.PythonTk()

	tm = TUI.TUIModel.getModel(True)
	addWindow(tm.tlSet)
	tm.tlSet.makeVisible('TUI.About TUI')

	root.lower()

	root.mainloop()
