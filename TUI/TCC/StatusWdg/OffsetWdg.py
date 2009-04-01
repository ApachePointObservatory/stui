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
"""
import Tkinter
import RO.CoordSys
import RO.StringUtil
import RO.Wdg
import TUI.TCC.TCCModel

_HelpPrefix = "Telescope/StatusWin.html#"
_DataWidth = 11

class OffsetWdg (Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """creates a new offset display frame

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.tccModel = TUI.TCC.TCCModel.Model()
        self.isArc = False
        gr = RO.Wdg.Gridder(self, sticky="w")

        gr.gridWdg("Obj")
        gr.gridWdg("Off")
        gr.startNewCol()

        # object offset (tcc arc offset)
        self.objLabelSet = []
        self.objOffWdgSet = [   # arc offset position
            RO.Wdg.DMSLabel(self,
                precision = 1,
                width = _DataWidth,
                helpText = "Object offset",
                helpURL = _HelpPrefix + "ObjOff",
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
            RO.Wdg.DMSLabel(self,
                precision = 1,
                width = _DataWidth,
                helpText = "Object offset shown in instrument x,y",
                helpURL = _HelpPrefix + "Obj",
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
        self.boreWdgSet = [
            RO.Wdg.DMSLabel(self,
                precision = 1,
                width = _DataWidth,
                helpText = "Position of boresight on instrument",
                helpURL = _HelpPrefix + "Boresight",
            )
            for ii in range(2)
        ]
        for ii in range(2):
            gr.gridWdg (
                label = (" Bore X", "Y")[ii],
                dataWdg = self.boreWdgSet[ii],
                units = RO.StringUtil.DMSStr,
            )

        # track coordsys and objInstAng changes for arc/sky offset
        self.tccModel.objSys.addValueCallback(self._objSysCallback)
        self.tccModel.objInstAng.addCallback(self._updObjXYOff)
        
        # track objArcOff
        self.tccModel.objArcOff.addCallback(self._objArcOffCallback)
    
        # track boresight position
        for ii in range(2):
            self.tccModel.boresight.addROWdg(self.boreWdgSet[ii], ind=ii)
        
    def _objSysCallback (self, keyVar):
        """Object coordinate system updated; update arc offset labels
        """
        csysObj = keyVar[0]
        # print "StatusWdg/OffsetWdg._objSysCallback%r" % ((csysObj, isCurrent),)
        posLabels = csysObj.posLabels()
        
        for ii in range(2):
            self.objLabelSet[ii]["text"] = posLabels[ii]

    def _objArcOffCallback(self, keyVar):
        isCurrent = keyVar.isCurrent
        objOffPVT = keyVar.valueList
        for ii in range(2):
            objOff = objOffPVT[ii].getPos()
            self.objOffWdgSet[ii].set(objOff, isCurrent)
        self._updObjXYOff()

    def _updObjXYOff(self, *args, **kargs):
        objInstAngPVT, isCurrent = self.tccModel.objInstAng[0]
        objInstAng = objInstAngPVT.getPos()
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

    dataList = (
        "ObjSys=ICRS, 0",
        "ObjNetPos=120.123450, 0.000000, 4494436859.66000, -2.345670, 0.000000, 4494436859.66000",
        "RotType=Obj",
    )

    TestData.testDispatcher.dispatch(dataList)

    tuiModel.reactor.run()
