#!/usr/local/bin/python
import RO.Wdg
import RO.InputCont

_HelpPrefix = "Telescope/SlewWin/KeepOffsetsPanel.html#"

class KeepOffsetWdg(RO.Wdg.OptionButtons):
	"""A widget showing which offsets to retain"""
	def __init__ (self, master=None, **kargs):
		RO.Wdg.OptionButtons.__init__(self,
			master,
			name = "Keep",
			optionList = (
				("Arc", "Object", False,
					"Retain the object (tcc arc) offset?",
					_HelpPrefix + "Arc"),
				("Boresight", "Boresight", False,
					"Retain the boresight position?"),
				("GCorr", "Guide Corr", False,
					"Retain the guiding correction?"),
				("Calib", "Calibration", True,
					"Retain the calibration correction?"),
			),
			helpURLPrefix = _HelpPrefix,
			headerText = "Keep Offsets",
			defButton = True,
			formatFunc = RO.InputCont.VMSQualFmt(),
			**kargs
		)


if __name__ == "__main__":
	import Tkinter
	def doPrint():
		print optFrame.getString()

	root = RO.Wdg.PythonTk()
	
	optFrame = KeepOffsetWdg(root)
	optFrame.pack()

	qualButton = Tkinter.Button (root, command=doPrint, text="Print")
	qualButton.pack()

	root.mainloop()
