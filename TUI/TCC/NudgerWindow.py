#!/usr/bin/env python
"""Graphical offsetter.

History:
2005-05-24 ROwen
2005-05-26 ROwen    Bug fix: _iimScaleCallback was totally broken, so the nudger box
                    labels were always to the right and above.
2005-06-03 ROwen    Improved uniformity of indentation.
2005-04-20 ROwen    All offsets are now computed.
2009-04-01 ROwen    Modified to use new TCC model.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import opscore.actor.keyvar
import TUI.TUIModel
import TUI.TCC.TCCModel

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = "TCC.Nudger",
        defGeom = "+50+507",
        resizable = False,
        visible = False,
        wdgFunc = NudgerWdg,
    )

_HelpPrefix = "Telescope/NudgerWin.html#"

_CnvRad = 50 # radius of drawing area of canvas
_MaxOffset = 5 # arcsec
_MaxAxisLabelWidth = 4 # chars; 4 is for Long
_ArrowTag = "arrow"

class _FakePosEvt:
    def __init__(self, xyPos):
        self.x, self.y = xyPos
        
# offset types to display
_OffTypes = ("Object", "Object XY", "Boresight", "Guide", "Guide XY")

# mapping from offset type to label; None means use user coordsys labels
_LabelDict = {
    "Object": None,
    "Object XY": ("X", "Y"),
    "Boresight": ("X", "Y"),
    "Guide": ("Az", "Alt"),
    "Guide XY": ("X", "Y"),
}

# mapping from displayed offset type to tcc offset type
_OffTCCTypeDict = {
    "Object": "arc",
    "Object XY": "arc",
    "Boresight": "boresight",
    "Guide": "guide",
    "Guide XY": "guide",
}

class NudgerWdg (Tkinter.Frame):
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)
        
        self.tuiModel = TUI.TUIModel.Model()
        self.tccModel = TUI.TCC.TCCModel.Model()
        
        self.arcSecPerPix = None
        self.iimScale = None
        self.xySign = (1, 1)
        self.offPix = None
        self.offArcSec = None
        self.objSysLabels = ("E", "N")
        
        textFrame = Tkinter.Frame(self)

        gr = RO.Wdg.Gridder(textFrame, sticky="w")
        
        maxOffNameLen = 0
        for offName in _OffTypes:
            maxOffNameLen = max(len(offName), maxOffNameLen)
        
        self.offTypeWdg = RO.Wdg.OptionMenu(
            master = textFrame,
            items = _OffTypes,
            defValue = "Guide XY",
            callFunc = self.updOffType,
            width = maxOffNameLen,
            helpText = "Type of offset",
            helpURL = _HelpPrefix + "OffType",
        )
        gr.gridWdg(False, self.offTypeWdg, colSpan=3)
        
        self.maxOffWdg = RO.Wdg.IntEntry(
            master = textFrame,
            minValue = 1,
            maxValue = _MaxOffset,
            defValue = 3,
            width = 2,
            callFunc = self.updMaxOff,
            helpText = "Maximum offset",
            helpURL = _HelpPrefix + "MaxOff",
        )
        gr.gridWdg("Max Off", self.maxOffWdg, '"')
        
        self.offAmtLabelSet = []
        self.offAmtWdgSet = []
        for ii in range(2):
            amtLabelWdg = RO.Wdg.StrLabel(
                master = textFrame,
                width = _MaxAxisLabelWidth + 4, # 4 is for " Off"
            )
            self.offAmtLabelSet.append(amtLabelWdg)
            
            offArcSecWdg = RO.Wdg.FloatLabel(
                master = textFrame,
                precision = 2,
                width = 5,
                helpText = "Size of offset",
                helpURL = _HelpPrefix + "OffAmt",
            )
            self.offAmtWdgSet.append(offArcSecWdg)
            
            gr.gridWdg(amtLabelWdg, offArcSecWdg, '"')

        textFrame.grid(row=0, column=0)
            
        cnvFrame = Tkinter.Frame(self)

        # canvas on which to display center dot and offset arrow
        cnvSize = (2 * _CnvRad) + 1
        self.cnv = Tkinter.Canvas(
            master = cnvFrame,
            width = cnvSize,
            height = cnvSize,
            borderwidth = 1,
            relief = "ridge",
            selectborderwidth = 0,
            highlightthickness = 0,
            cursor = "crosshair",
        )
        self.cnv.helpText = "Mouse up to offset; drag outside to cancel"
        self.cnv.grid(row=1, column=1, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        RO.Wdg.addCtxMenu(
            wdg = self.cnv,
            helpURL = _HelpPrefix + "Canvas",
        )

        # create xyLabelSet:
        # first index is 0 for x, 1 for y
        # second index is 0 for sign=1, 1 for sign=-1 (mirror image)
        xLabelSet = []
        cols = (2, 0)
        for ii in range(2):
            xLabel = RO.Wdg.StrLabel(
                master = cnvFrame,
                width = _MaxAxisLabelWidth,
                anchor = ("w", "e")[ii],
            )
            xLabelSet.append(xLabel)
            xLabel.grid(row=1, column=cols[ii])
            
        yLabelSet = []
        rows = (0, 2)
        for ii in range(2):
            yLabel = RO.Wdg.StrLabel(
                master = cnvFrame,
                width = _MaxAxisLabelWidth,
                anchor = "c",
            )
            yLabelSet.append(yLabel)
            yLabel.grid(row=rows[ii], column=1)
        self.xyLabelSet = (xLabelSet, yLabelSet)

        cnvFrame.grid(row=0, column=1)
        
        # draw gray crosshairs
        kargs = {
            "stipple": "gray50",
        }
        self.cnv.create_line(_CnvRad, 0, _CnvRad, cnvSize, **kargs)
        self.cnv.create_line(0, _CnvRad, cnvSize, _CnvRad, **kargs)
    
        self.statusBar = RO.Wdg.StatusBar(
            master = self,
            dispatcher = self.tuiModel.dispatcher,
            prefs = self.tuiModel.prefs,
            playCmdSounds = True,
            helpURL = _HelpPrefix + "StatusBar",
        )
        self.statusBar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.cnv.bind('<B1-Motion>', self.drawContinue)
        # the following prevents the display from blanking
        # when the button is pressed once (I tried trapping and
        # discarding <Button>, as a faster solutionn, but it didn't work)
        self.cnv.bind('<ButtonPress-1>', self.drawBegin)
        self.cnv.bind('<ButtonRelease-1>', self.drawEnd)
        
        self.tccModel.iimScale.addCallback(self._iimScaleCallback)
        self.tccModel.objSys.addCallback(self._objSysCallback, 0)

        self.updMaxOff()
        self.updOffType()

    def pixFromArcSec(self, xyArcSec):
        """Convert a point from x,y arcsec (x right, y up) to canvas x,y.
        """
        if self.arcSecPerPix == None:
            raise RuntimeError("Unknown scale")

        xyPix = (
            _CnvRad + ( self.xySign[0] * xyArcSec[0] / self.arcSecPerPix),
            _CnvRad + (-self.xySign[1] * xyArcSec[1] / self.arcSecPerPix),
        )
        return xyPix

    def arcSecFromPix(self, xyPix):
        """Convert a point from canvas x,y to x,y arcsec (x right, y up).
        """
        if self.arcSecPerPix == None:
            raise RuntimeError("Unknown scale")
        
        xyArcSec = (
            (xyPix[0] - _CnvRad) *  self.xySign[0] * self.arcSecPerPix,
            (xyPix[1] - _CnvRad) * -self.xySign[1] * self.arcSecPerPix,
        )
        return xyArcSec
    
    def clear(self, evt=None):
        self.cnv.delete(_ArrowTag)
        for ii in range(2):
            self.offAmtWdgSet[ii].set(None)
        self.offPix = None
        self.offArcSec = None
    
    def drawBegin(self, evt):
        self.drawContinue(evt)
    
    def drawContinue(self, evt):
        if self.arcSecPerPix == None:
            self.clear()
            return
        
        self.offPix = (evt.x, evt.y)
        maxPix = (_CnvRad*2)
        if (self.offPix[0] < 0) or (self.offPix[1] < 0) \
           or (self.offPix[0] > maxPix) or (self.offPix[1] > maxPix):
            self.clear()
            return

        self.cnv.delete(_ArrowTag)
        self.cnv.create_line(
            _CnvRad, _CnvRad, evt.x, evt.y, arrow="last", tag=_ArrowTag,
        )
        self.updOffAmt()
    
    def drawEnd(self, evt=None):
        if self.offArcSec == None:
            return
    
        offType = self.offTypeWdg.getString()
        tccOffType = _OffTCCTypeDict[offType]
        offDeg = [val / 3600.0 for val in self.offArcSec]
        
        # if necessary, rotate offset appropriately
        try:
            if offType == "Guide XY":
                offDeg = self.azAltFromInst(offDeg)
            elif offType == "Object XY":
                offDeg = self.objFromInst(offDeg)
        except ValueError, e:
            self.statusBar.setMsg("Failed: %s" % (e,), severity=RO.Constants.sevError)
            self.statusBar.playCmdFailed()
            return
        
        cmdStr = "offset/computed %s %.7f, %.7f" % (tccOffType, offDeg[0], offDeg[1])
        cmdVar = opscore.actor.keyvar.CmdVar (
            actor = "tcc",
            cmdStr = cmdStr,
            timeLim = 10,
            timeLimKeyword="SlewDuration",
            isRefresh = False,
        )
        self.statusBar.doCmd(cmdVar)
    
    def azAltFromInst(self, offVec):
        """Rotates offVec from inst to az/alt coords.
        Raises ValueError if cannot compute.
        """
        spiderInstAngPVT, isCurrent = self.tccModel.spiderInstAng[0]
        spiderInstAng = spiderInstAngPVT.getPos()
        if not isCurrent or spiderInstAng == None:
            raise ValueError, "spiderInstAng unknown"
        if None in offVec:
            raise ValueError, "bug: unknown offset"
        return RO.MathUtil.rot2D(offVec, -spiderInstAng)

    def objFromInst(self, offVec):
        """Rotates objPos from inst to obj coords.
        Raises ValueError if cannot compute.
        """
        objInstAngPVT, isCurrent = self.tccModel.objInstAng[0]
        objInstAng = objInstAngPVT.getPos()
        if not isCurrent or objInstAng == None:
            raise ValueError, "objInstAng unknown"
        if None in offVec:
            raise ValueError, "bug: unknown offset"
        return RO.MathUtil.rot2D(offVec, -objInstAng)

    def _iimScaleCallback(self, keyVar):
        iimScale = keyVar.valueList
        if None in iimScale:
            return
    
        if self.iimScale != iimScale:
            # if scale has changed then this is probably a new instrument
            # so clear the existing offset and make sure the labels
            # are displayed on the correct sides of the nudger box
            self.iimScale = iimScale
            self.xySign = [RO.MathUtil.sign(scl) for scl in iimScale]
            self.clear()
            self.updOffType()

    def _objSysCallback (self, keyVar=None):
        """Updates the display when the coordinate system is changed.
        """
        self.objSysLabels = self.tccModel.csysObj.posLabels()
        self.updOffType()
    
    def updMaxOff(self, wdg=None):
        maxOff = self.maxOffWdg.getNum()
        
        if maxOff == 0:
            self.arcSecPerPix = None
            self.clear()
            return
        
        self.arcSecPerPix = float(maxOff) / float(_CnvRad)
        offArcSec = self.offArcSec
        if offArcSec != None:
            offPix = self.pixFromArcSec(offArcSec)
            self.drawContinue(_FakePosEvt(offPix))
    
    def updOffAmt(self):
        if self.offPix == None:
            self.clear()
            return
            
        self.offArcSec = self.arcSecFromPix(self.offPix)
        for ii in range(2):
            self.offAmtWdgSet[ii].set(self.offArcSec[ii])       

    def updOffType(self, wdg=None):
        offType = self.offTypeWdg.getString()
        xyLab = _LabelDict[offType]
        if xyLab == None:
            xyLab = self.objSysLabels
            
        for ii in range(2):
            lab = xyLab[ii]
            sign = self.xySign[ii]
            labSet = self.xyLabelSet[ii]
            
            if sign > 0:
                labSet[0].set(lab)
                labSet[1].set("")
            else:
                labSet[1].set(lab)
                labSet[0].set("")
            self.offAmtLabelSet[ii].set(lab + " Off")
            self.offAmtWdgSet[ii].helpText = "Size of offset in %s" % (lab.lower())
        self.clear()


if __name__ == '__main__':
    import TUI.Base.TestDispatcher

    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher(actor="tcc")
    tuiModel = testDispatcher.tuiModel

    testFrame = NudgerWdg(tuiModel.tkRoot)
    testFrame.pack()
    tuiModel.tkRoot.resizable(width=0, height=0)

    dataList = (
        "ObjSys=Gal, 2000",
        "ObjInstAng=30.0, 0.0, 1000.0",
        "SpiderInstAng=-30.0, 0.0, 1000.0",
    )

    testDispatcher.dispatch(dataList)

    tuiModel.reactor.run()
