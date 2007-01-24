#!/usr/bin/env python
"""DIS slitviewer window

History:
2005-06-22 ROwen
2005-06-27 ROwen    Removed unused _HelpURL.
2005-07-14 ROwen    Removed local test mode support.
2006-04-13 ROwen    Modified for updated GuideTest.runDownload.
"""
import RO.Alg
import GuideWdg

def addWindow(tlSet):
    return tlSet.createToplevel (
        name = "Guide.DIS Slitviewer",
        defGeom = "+452+280",
        resizable = True,
        wdgFunc = RO.Alg.GenericCallback(GuideWdg.GuideWdg, actor="dcam"),
        visible = False,
    )
    

if __name__ == "__main__":
    import RO.Wdg
    import GuideTest
    
    root = RO.Wdg.PythonTk()

    GuideTest.init("dcam")

    testTL = addWindow(GuideTest.tuiModel.tlSet)
    testTL.makeVisible()
    testTL.wait_visibility() # must be visible to download images
    testFrame = testTL.getWdg()

    GuideTest.runDownload(
        basePath = "keep/ecam/UT050422/",
        imPrefix = "e",
        startNum = 101,
        numImages = 3,
        waitMs = 2500,
    )

    root.mainloop()
