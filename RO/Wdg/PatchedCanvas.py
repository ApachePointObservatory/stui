#!/usr/local/bin/python
"""A version of the Canvas class that draws correctly
on unix, MacOS and MacOS X.

This module is now deprecated because the Mac corrections are no longer needed
as of some Tk version <= 8.4.7. Please use Tkinter.Canvas.

History:
2002-11-12 ROwen	First version derived from RO.CanvasUtil.py
2002-12-20 ROwen	Removed unused local variable.
2004-08-11 ROwen	Define __all__ to restrict import.
2004-10-22 ROwen`	Disabled corrections and now issues a deprecation warning.
"""
__all__ = ['PatchedCanvas']

import warnings
import Tkinter

class PatchedCanvas(Tkinter.Canvas):
	def __init__(self, *args, **kargs):
		Tkinter.Canvas.__init__(self, *args, **kargs)
		
		warnings.warn("RO.Wdg.PatchedCanvas is obsolete; please use Tkinter.Canvas instead.",
			category = DeprecationWarning,
			stacklevel = 2,
		)


if __name__ == "__main__":
	root = Tkinter.Tk()
	c = PatchedCanvas(root, width=200, height=200)
	c.pack()
	
	objWidth = 30
	yPos = 10
	for yPos, lineWidth in ((10, 1), (50, 2), (90, 3), (130, 4)):
		for xPos in (10, 50, 90):
			c.create_oval(xPos, yPos, xPos+objWidth, yPos+objWidth, width=lineWidth)
			c.create_rectangle(xPos, yPos, xPos+objWidth, yPos+objWidth, width=lineWidth)
			c.create_line(xPos, yPos, xPos+objWidth, yPos+objWidth, width=lineWidth)
			c.create_line(xPos, yPos+objWidth, xPos+objWidth, yPos, width=lineWidth)
			c.create_line(xPos, yPos+(objWidth/2), xPos+objWidth, yPos+(objWidth/2), width=lineWidth)
			c.create_line(xPos+(objWidth/2), yPos, xPos+(objWidth/2), yPos+objWidth, width=lineWidth)
	
	root.mainloop()