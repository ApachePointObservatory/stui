#!/usr/bin/env python
"""Displays arc/sky and boresight offsets.

To do:
- In the test case dispatch reasonable data

History:
2003-04-04 ROwen
2003-04-14 ROwen    Modified to show Obj and Obj XY offset at the same time
2003-06-09 Rowen    Removed dispatcher arg.
2003-06-11 ROwen    Modified to use new tccModel objSys.
2003-06-12 ROwen    Added helpText entries.
2003-06-25 ROwen    Modified test case to handle message data as a dict
2004-02-04 ROwen    Modified _HelpURL to match minor help reorg.
2004-05-18 ROwen    Bug fix: OffsetWdg._updObjXYOff used "except a, b:" instead of "except (a, b):"
                    to catch two classes of exception, so the second would not be caught.
                    Removed unused constant _ArcLabelWidth.
2009-07-19 ROwen    Modified to work with new KeyVar and the way it handles PVTs.
2009-09-09 ROwen    Improved the test data to show meaningful values.
2010-03-11 ROwen    Added Focus, Scale and Guiding (two of which were moved from MiscWdg.py).
2010-03-12 ROwen    Changed to use Models.getModel.
2010-03-19 ROwen    Simplified help URLs to all point to the same section.
2010-11-04 ROwen    Changed Obj Off to Object Arc Off.
2010-11-05 ROwen    Bug fix: the code that displays arc offset mishandled unknown data.
2010-11-22 ROwen    Changed Scale display from scaleFac to (scaleFac - 1) * 1e6.
2011-02-16 ROwen    Moved Focus, Scale and Guiding state from here to MiscWdg.
                    Tightened the layout a bit.
                    Made the display expand to the right of the displayed data.
"""
import Tkinter
import RO.CnvUtil
import RO.CoordSys
import RO.StringUtil
import RO.Wdg
import TUI.Models

_HelpURL = "Telescope/StatusWin.html#Offsets"
_DataWidth = 10

class OffsetWdg (Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """creates a new offset display frame

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.tccModel = TUI.Models.getModel("tcc")
        gr = RO.Wdg.Gridder(self, sticky="w")

        gr.gridWdg("Object")
        gr.gridWdg("Arc Off")
        gr.startNewCol()
        
        MountLabels = ("Az", "Alt", "Rot")

        # object offset (tcc arc offset)
        self.objLabelSet = []
        self.objOffWdgSet = [   # arc offset position
            RO.Wdg.DMSLabel(
                master = self,
                precision = 1,
                width = _DataWidth,
                helpText = "Object arc offset",
                helpURL = _HelpURL,
            )
            for ii in range(2)
        ]
        for ii in range(2):
            wdgSet = gr.gridWdg (
                label = "",
                dataWdg = self.objOffWdgSet[ii],
                units = RO.StringUtil.DMSStr,
            )
            wdgSet.labelWdg.configure(width=4, anchor="e")
            self.objLabelSet.append(wdgSet.labelWdg)
        
        # sky offset
        gr.startNewCol()
        self.objXYOffWdgSet = [
            RO.Wdg.DMSLabel(
                master = self,
                precision = 1,
                width = _DataWidth,
                helpText = "Object offset shown in instrument x,y",
                helpURL = _HelpURL,
            )
            for ii in range(2)
        ]
        for ii in range(2):
            wdgSet = gr.gridWdg (
                label = ("(X", "(Y")[ii],
                dataWdg = self.objXYOffWdgSet[ii],
                units = RO.StringUtil.DMSStr + ")",
            )

        # boresight
        gr.startNewCol()
        gr.gridWdg("Bore")
        gr.startNewCol()
        self.boreWdgSet = [
            RO.Wdg.DMSLabel(
                master = self,
                precision = 1,
                width = _DataWidth,
                helpText = "Position of boresight on instrument",
                helpURL = _HelpURL,
            )
            for ii in range(2)
        ]
        for ii in range(2):
            gr.gridWdg (
                label = ("X", "Y")[ii],
                dataWdg = self.boreWdgSet[ii],
                units = RO.StringUtil.DMSStr,
            )

        # allow the last+1 column to grow to fill the available space
        self.columnconfigure(gr.getMaxNextCol(), weight=1)

        self.tccModel.objSys.addCallback(self._objSysCallback)
        self.tccModel.objInstAng.addCallback(self._updObjXYOff)
        self.tccModel.objArcOff.addCallback(self._objArcOffCallback)
        self.tccModel.boresight.addValueListCallback([wdg.set for wdg in self.boreWdgSet], cnvFunc=RO.CnvUtil.posFromPVT)
        
    def _objSysCallback (self, keyVar=None):
        """Object coordinate system updated; update arc offset labels
        """
        # print "%s._objSysCallback(%s)" % (self.__class__.__name__, keyVar)
        posLabels = self.tccModel.csysObj.posLabels()
        
        for ii in range(2):
            self.objLabelSet[ii]["text"] = posLabels[ii]

    def _objArcOffCallback(self, keyVar):
        isCurrent = keyVar.isCurrent
        for ii in range(2):
            objOff = RO.CnvUtil.posFromPVT(keyVar[ii])
            self.objOffWdgSet[ii].set(objOff, isCurrent)
        self._updObjXYOff()

    def _updObjXYOff(self, *args, **kargs):
        objInstAng = RO.CnvUtil.posFromPVT(self.tccModel.objInstAng[0])
        isCurrent = self.tccModel.objInstAng.isCurrent
        objOff = [None, None]
        for ii in range(2):
            objOff[ii], arcCurr = self.objOffWdgSet[ii].get()
            isCurrent = isCurrent and arcCurr
        try:
            objXYOff = RO.MathUtil.rot2D(objOff, objInstAng)
        except (TypeError, ValueError):
            objXYOff = (None, None)
        for ii in range(2):
            self.objXYOffWdgSet[ii].set(objXYOff[ii], isCurrent)
       
       
if __name__ == "__main__":
    import TestData

    tuiModel = TestData.tuiModel

    testFrame = OffsetWdg(tuiModel.tkRoot)
    testFrame.pack()

    TestData.init()

    tuiModel.reactor.run()
