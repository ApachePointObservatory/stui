#!/usr/bin/env python
"""TripleSpec slitviewer window

History:
2008-03-14 ROwen
"""
import RO.Alg
import GuideWdg

def addWindow(tlSet):
    return tlSet.createToplevel (
        name = "Guide.TripleSpec Slitviewer",
        defGeom = "+452+280",
        resizable = True,
        wdgFunc = RO.Alg.GenericCallback(GuideWdg.GuideWdg, actor="tcam"),
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
