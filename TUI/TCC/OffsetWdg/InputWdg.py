#!/usr/bin/env python
"""Simple offset control.
Allows changing the boresight position
or setting the arc offset in inst xy.

History:
2003-04-02 ROwen
2003-04-14 ROwen    Renamed Sky->Object XY; added Object.
2003-06-09 Rowen    Removed dispatcher arg.
2003-06-11 ROwen    Modified to use new tccModel.objSys
2003-06-12 ROwen    Added helpText entries.
2003-06-17 ROwen    Reordered abs and rel to match Remark.
2003-06-25 ROwen    Modified test case to handle message data as a dict.
2003-07-10 ROwen    Modified to use overhauled RO.InputCont.
2003-10-14 ROwen    Modified to use computed offsets (by APO request).
2003-11-06 ROwen    Changed Offset.html to OffsetWin.html
2006-04-14 ROwen    Added explicit default to absOrRelWdg (required
                    due to recent changes in RO.Wdg.RadiobuttonSet).
2009-04-01 ROwen    Modified for tuisdss.
2010-03-12 ROwen    Changed to use Models.getModel.
2010-06-28 ROwen    Fixed an invalid variable reference in _objFromInst (thanks to pychecker).
"""
import Tkinter
import RO.CnvUtil
import RO.CoordSys
import RO.InputCont
import RO.StringUtil
import RO.Wdg
import TUI.Models

_HelpPrefix = "Telescope/OffsetWin.html#"
_MaxOffset = 3600 # arcsec

class InputWdg(RO.Wdg.InputContFrame):
    def __init__ (self,
        master = None,
     **kargs):
        """creates a new widget for specifying simple offsets

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        self.tccModel = TUI.Models.getModel("tcc")
        gr = RO.Wdg.Gridder(self, sticky="w")
        self.userLabels = ("RA", "Dec")
        
        # offset type
        self.offTypeWdg = RO.Wdg.OptionMenu (
            self,
            items = (
                "Object",
                "Object XY",
                None,
                "Boresight"
            ),
            defValue = "Object",
            callFunc = self._offTypeChanged,
            helpText = (
                "Adjust object position",
                "Adjust obj. pos. in inst. x,y",
                None,
                "Adjust boresight position",
            ),
            helpURL = _HelpPrefix + "OffType",
        )
        gr.gridWdg (
            label = "Type",
            dataWdg = self.offTypeWdg,
            colSpan = 2,
        )
        lastCol = gr.getNextCol()-1
        self.columnconfigure(lastCol, weight=1)
        
        # position entry: use relative DMS entry fields
        self.offWdgSet = [None, None]
        self.offLabelSet = [None, None]
        for ii in range(2):
            unitsVar = Tkinter.StringVar()
            wdg = RO.Wdg.DMSEntry(self,
                    minValue = -_MaxOffset,
                    maxValue = _MaxOffset,
                    defValue = None,
                    isHours = False,
                    isRelative = True,
                    helpText = "Amount of offset",
                    helpURL = _HelpPrefix + "OffAmt",
                    unitsVar = unitsVar,
            )
            label = Tkinter.Label(self, width=6, anchor="e")
            self.offWdgSet[ii] = wdg
            self.offLabelSet[ii] = label
            gr.gridWdg(
                label = label,
                dataWdg = wdg,
                units = wdg.unitsVar,
            )
    
        # relative or absolute
        frame = Tkinter.Frame(self)
        self.absOrRelWdg = RO.Wdg.RadiobuttonSet (
            frame,
            textList = ("Abs", "Rel"),
            defValue = "Rel",
            side = "left",
            helpText = (
                "Replace the existing offset",
                "Add amount to existing offset",
            ),
            helpURL = _HelpPrefix + "absOrRel",
        )
        gr.gridWdg (
            dataWdg = frame,
            colSpan = 3,
        )
        
        self.tccModel.objSys.addCallback(self._objSysCallback)

        # create a set of input widget containers
        # this makes it easy to retrieve a command
        # and also to get and set all data using a value dictionary
        def formatCmd(inputCont):
            valDict = inputCont.getValueDict()
            offType = valDict["type"]
            offAmt = valDict["amount"]
            relOrAbs = valDict["absOrRel"]

            def arcSecToDeg(str):
                if not str:
                    return 0.0
                return RO.StringUtil.secFromDMSStr(str) / 3600.0
            offAmt = [arcSecToDeg(amtStr) for amtStr in offAmt]
    
            if offType == "Object XY":
                offAmt = self._objFromInst(offAmt)
            tccType = {
                "Object":"arc",
                "Object XY":"arc",
                "Boresight":"boresight",
            }[offType]
    
            if relOrAbs == "Abs":
                relStr = "/pabs"
            else:
                relStr = ""
            return "offset %s %.7f, %.7f%s/computed" % (tccType, offAmt[0], offAmt[1], relStr)
        
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = "type",
                    wdgs = self.offTypeWdg,
                    omitDef = False,
                ),
                RO.InputCont.WdgCont (
                    name = "amount",
                    wdgs = self.offWdgSet,
                    omitDef = False,
                ),                  
                RO.InputCont.WdgCont (
                    name = "absOrRel",
                    wdgs = self.absOrRelWdg,
                    omitDef = False,
                ),
            ],
            formatFunc = formatCmd,
        )

        # initialize display
        self.restoreDefault()
    
    def _offTypeChanged(self, *args):
        offType = self.offTypeWdg.getString()
        if offType == "Object":
            offLabels = self.userLabels
        else:
            offLabels = ("Inst X", "Inst Y")
        for ii in range(2):
            self.offLabelSet[ii]["text"] = offLabels[ii]
    
    def _objSysCallback (self, keyVar=None):
        """Coordinate system changed; update the displayed axis labels
        """
        self.userLabels = self.tccModel.csysObj.posLabels()
        
        self._offTypeChanged()
    
    def _objFromInst(self, offVec):
        """Rotates objPos from inst to obj coords.
        Raises ValueError if cannot compute.
        """
        objInstAngPVT = self.tccModel.objInstAng[0]
        isCurrent = self.tccModel.objInstAng.isCurrent
        objInstAng = RO.CnvUtil.posFromPVT(objInstAngPVT)
        if not isCurrent or objInstAng == None:
            raise ValueError, "objInstAng unknown"
        if None in offVec:
            raise ValueError, "bug: unknown offset"
        return RO.MathUtil.rot2D(offVec, -objInstAng)
    
    def clear(self):
        for wdg in self.offWdgSet:
            wdg.set("")

    def getCommand(self):
        return self.getString()
            
    def neatenDisplay(self):
        for wdg in self.offWdgSet:
            wdg.neatenDisplay()


if __name__ == "__main__":
    import TUI.Base.TestDispatcher

    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher(actor="tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot

    testFrame = InputWdg(root)
    testFrame.pack(anchor="nw")
    tuiModel.tkRoot.resizable(width=0, height=0)
    
    def doPrint():
        print testFrame.getCommand()
        
    def defaultCommand():
        testFrame.restoreDefault()

    buttonFrame = Tkinter.Frame(root)
    Tkinter.Button (buttonFrame, command=doPrint, text="Print").pack(side="left")
    Tkinter.Button (buttonFrame, command=defaultCommand, text="Default").pack(side="left")
    Tkinter.Button (buttonFrame, command=testFrame.neatenDisplay, text="Neaten").pack(side="left")
    buttonFrame.pack()

    dataList = (
        "ObjInstAng=30.0, 0.0, 1.0",
    )

    testDispatcher.dispatch(dataList)

    tuiModel.reactor.run()
