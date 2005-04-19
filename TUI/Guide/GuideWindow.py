#!/usr/local/bin/python
"""Guiding windows

History:
2005-03-30 ROwen
2005-04-11 ROwen	Modified for GCamModel->GuideModel
2005-04-12 ROwen	Improved test code.
2005-04-18 ROwen	Modified to use updated test code.
"""
import RO.Alg
import TUI.TUIModel
# import TUI.TCC.TCCModel
import GuideModel
import GuideWdg

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "Guide.GCam",
		defGeom = "+452+280",
		resizable = True,
		wdgFunc = RO.Alg.GenericCallback (
			GuideWdg.GuideWdg,
			actor = "gcam",
		),
		visible = False,
	)
	
	tlSet.createToplevel (
		name = "Guide.ECam",
		defGeom = "+676+280",
		resizable = True,
		wdgFunc = RO.Alg.GenericCallback (
			GuideWdg.GuideWdg,
			actor = "ecam",
		),
		visible = False,
	)


if __name__ == "__main__":
	import GuideTest
	import RO.Wdg

	root = RO.Wdg.PythonTk()
	GuideWdg._LocalMode = True
	GuideTest.init()

	addWindow(GuideTest.tuiModel.tlSet)

	gcamTL = GuideTest.tuiModel.tlSet.getToplevel("Guide.GCam")
	gcamTL.makeVisible()
	gcamFrame = gcamTL.getWdg()

	ecamTL = GuideTest.tuiModel.tlSet.getToplevel("Guide.ECam")
	ecamTL.makeVisible()
	ecamFrame = ecamTL.getWdg()
	
	GuideTest.run()
	
	root.mainloop()
