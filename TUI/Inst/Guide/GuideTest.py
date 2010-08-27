#!/usr/bin/env python
"""Guide test code that crudely substitutes for the hub

To do:
- make the whole thing an object

History:
2005-01-31 ROwen
2005-02-08 ROwen    Updated for PyGuide 1.2.
2005-02-22 ROwen    Fixed centroid output (had not been updated to match new star format).
2005-03-25 ROwen    Updated for new keywords. Stopped using float("nan").
2005-03-28 ROwen    Updated again for improved files and star keywords.
2005-04-11 ROwen    Modified for GCamModel->GuideModel.
                    Adjusted for 2005-04-01 findStars.
2005-04-12 ROwen    Made safe to import even when not being used.
2005-04-18 ROwen    Improved test code to increment cmID and offered a separate
                    optional init function before run (renamed from start).
2005-05-20 ROwen    Modified for PyGuide 1.3.
                    Stopped outputting obsolete centroidPyGuideConfig keyword.
                    Added _Verbosity to set verbosity of PyGuide calls.
                    Modified to send thesh to PyGuide.centroid
                    Modified to output xxDefxx keywords at startup.
2005-05-25 ROwen    Added the requirement to specify actor.
2005-06-13 ROwen    Added runDownload for a more realistic way to get lots of images.
2005-06-16 ROwen    Modified to import (with warnings) if PyGuide missing.
2005-06-17 ROwen    Bug fix: init failed if no PyGuide.
2005-06-22 ROwen    Changed init argument doFTP to isLocal.
                    Modified to set GuideWdg._LocalMode and _HistLength.
2005-06-24 ROwen    Added nFiles argument to runLocalFiles.
2005-07-08 ROwen    Modified for http download: changed imageRoot to httpRoot.
2005-07-14 ROwen    Removed isLocal mode.
2006-04-13 ROwen    runDownload: added imPrefix and removed maskNum argument.
                    nextDownload: removed maskNum.
2006-05-24 ROwen    setParams: added mode, removed count.
2007-04-24 ROwen    Removed unused import of numarray.
2009-03-31 ROwen    Modified to use twisted timers.
2009-07-15 ROwen    Modified to work with sdss code.
2009-11-10 ROwen    Removed obsolete code (leaving almost nothing).
2010-01-25 ROwen    Added guideState and two gcamera keywords.
"""
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("guider")
tuiModel = testDispatcher.tuiModel

GuiderMainDataList = (
    "expTime = 5.0",
    "gprobeBits=0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x2",
    "guideEnable=True, True, False",
    "guideState=On",
    'gprobes="(1=True)","(2=True)","(3=True)","(4=True)","(5=True)","(6=True)","(7=True)","(8=True)","(9=True)","(10=True)","(11=True)","(12=True)","(13=True)","(14=True)","(15=True)","(16=True)","(17=False)"',
)

GCameraMainDataList = (
    "exposureState = integrating, 9, 10",
    "simulating = On, /foo/bar/images, 5"
)

def start():
    testDispatcher.dispatch(GuiderMainDataList)
    testDispatcher.dispatch(GCameraMainDataList, actor="gcamera")

