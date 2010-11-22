#!/usr/bin/env python
"""Correction widgets

These show the measured error and proposed correction from the guider,
control whether automatic correction is enabled
and allow the user to specify an additional correction.

History:
2010-11-19 ROwen    Extracted from GuideWdg and overhauled.
2010-11-22 ROwen    Added didCorrWdg to show if the guider applied the correction.
                    Added netCorrWdg to display correction.
                    Changed Scale scaling from 1e2 to 1e6.
"""
import atexit
import itertools
import os
import sys
import traceback
import Tkinter

import numpy

import opscore.actor
import RO.Alg
import RO.CanvasUtil
import RO.Constants
import RO.DS9
import RO.MathUtil
import RO.PhysConst
import RO.OS
import RO.Prefs
import RO.StringUtil
import RO.Wdg
import TUI.Models
import CmdInfo

class ItemInfo(object):
    """List of widgets showing measured error, etc. for single item that can be corrected
    
    Items include RA, Dec, rotator, focus and scale.
    """
    WdgWidth = 7
    def __init__(self, master, label, descr, units, callFunc=None,
        precision = 2, minValue=None, maxValue=None, helpURL=None):
        """Create an ItemInfo
        
        Inputs:
        - master: master widget
        - label: label for title widget
        - descr: short description for help string
        - units: units of this item
        - callFunc: a function to call when userCorrWdg is modified
        - precision: number of digits after the decimal point
        - minValue: minimum value for userCorrWdg
        - maxValue: maximum value for userCorrWdg
        - helpURL: help URL
        """
        self.label = label
        self.descr = descr
        self.units = units
        
        defFormat = "%%0.%df" % (precision,)
        
        self.netCorrWdg = RO.Wdg.FloatLabel(
            master = master,
            precision = precision,
            width = self.WdgWidth,
            helpText = "net correction for %s" % (self.descr,),
            helpURL = helpURL,
        )
        self.measWdg = RO.Wdg.FloatEntry(
            master = master,
            defFormat = defFormat,
            readOnly = True,
            width = self.WdgWidth,
            helpText = "measured error in %s" % (self.descr,),
            helpURL = helpURL,
        )
        self.corrWdg = RO.Wdg.FloatEntry(
            master = master,
            defFormat = defFormat,
            readOnly = True,
            width = self.WdgWidth,
            helpText = "guider correction for %s" % (self.descr,),
            helpURL = helpURL,
        )
        self.didCorrWdg = RO.Wdg.StrLabel(
            master = master,
            width = 3,
            anchor = "w",
            helpText = "did guider correct %s?" % (self.descr,),
            helpURL = helpURL,
        )
        self.userCorrWdg = RO.Wdg.FloatEntry(
            master = master,
            callFunc = callFunc,
            autoIsCurrent = True,
            defFormat = defFormat,
            minValue = minValue,
            maxValue = maxValue,
            width = self.WdgWidth,
            helpText = "user-specified correction for %s" % (self.descr,),
            helpURL = helpURL,
        )

    @property
    def isClear(self):
        """Return True if all user correction widgets are zero or blank.
        """
        if self.userCorrWdg.getString() != "":
            return False
        return True

    def clear(self):
        if not self.isClear:
            self.userCorrWdg.clear()

    def getUserCorr(self):
        return self.userCorrWdg.getNum()


class CategoryInfo(object):
    """Set of widgets to enable/disable, show and apply corrections for one category of items
    
    Subclass for explicit categories. Subclasses must:
    - add 1 or more items (do this before adding callbacks to keyword variables)
    - grid the widgets using gridRow
    - bind _corrCallback and _measCallback to the appropriate guider keywords (e.g. axisChange and axisError)
    - override getUserOffsetCommands
    """
    def __init__(self, master, label, descr, enableCallFunc, userCallFunc, helpURL):
        """Create a CategoryInfo
        
        Inputs:
        - master: master (parent) widget
        - label: label for enable widget
        - descr: description of item
        - enableCallFunc: function to call when enableWdg toggled
        - userCallFunc: a function to call when the user modifies a correction value
        - helpURL: URL for help
        """
        self.master = master
        self.label = label
        self.descr = descr
        self.userCallFunc = userCallFunc
        self.helpURL = helpURL
        
        self.enableWdg = RO.Wdg.Checkbutton(
            master = master,
            text = self.label,
            defValue = True,
            callFunc = enableCallFunc,
            helpText = "Enable automatic correction of %s" % (self.descr,),
            helpURL = helpURL,
        )
        
        self.itemInfoList = []

    def _addItem(self, units="", label=None, descr=None, precision=2, minValue=None, maxValue=None):
        """Add an item

        Inputs:
        - units: units of this item
        - label: label for title widget; defaults to None
        - descr: short description for help string; defaults to category descr
        - precision: number of digits after the decimal point
        - minValue: minimum value for userCorrWdg
        - maxValue: maximum value for userCorrWdg
        """
        if descr == None:
            descr = self.descr
        self.itemInfoList.append(ItemInfo(
            master = self.master,
            label = label,
            descr = descr,
            units = units,
            callFunc = self.userCallFunc,
            precision = precision,
            minValue = minValue,
            maxValue = maxValue,
            helpURL = self.helpURL,
        ))
    
    def clear(self):
        for itemInfo in self.itemInfoList:
            itemInfo.clear()

    def getUserOffsetCommands(self):
        """Return a list of 0 or more commands to implement the user's requested offsetss
        
        The returned data is a list of tuples, each containing:
        - actor: name of actor
        - cmdStr: command string
        - indList: a list of item indices
        
        Must be overridden by subclass
        """
        raise NotImplementedError("Subclass must override")

    def gridRow(self, row, itemInd=0, includeEnableWdg=True):
        """Grid one row of widgets
        """
        label = self.itemInfoList[itemInd].label

        col = 0
        colSpan = 1
        if includeEnableWdg:
            if not label:
                colSpan = 2
            self.enableWdg.grid(row=row, column=col, columnspan=colSpan, sticky="w")
        col += colSpan
        
        if label:
            axisLabel = RO.Wdg.StrLabel(master=self.master, text=label)
            axisLabel.grid(row=row, column=col, sticky="e")
            col += 1
        
        itemInfo = self.itemInfoList[itemInd]
        
        itemInfo.netCorrWdg.grid(row=row, column=col)
        col += 1
        itemInfo.measWdg.grid(row=row, column=col)
        col += 1
        itemInfo.corrWdg.grid(row=row, column=col)
        col += 1
        itemInfo.didCorrWdg.grid(row=row, column=col)
        col += 1
        itemInfo.userCorrWdg.grid(row=row, column=col)
        col += 1
        unitsLabel = RO.Wdg.StrLabel(master=self.master, text=itemInfo.units)
        unitsLabel.grid(row=row, column=col, sticky="w")
        col += 1

    @property
    def isClear(self):
        """Return True if all user correction widgets are zero or blank.
        """
        for itemInfo in self.itemInfoList:
            if not itemInfo.isClear:
                return False
        return True

    @property
    def numItems(self):
        """Return the number of items
        """
        return len(self.itemInfoList)

    def startUserOffsetCommands(self, sr):
        """Start a set of 0 or more commands that will implement the user's requested offsets
        """
        cmdVarList = []
        cmdList = self.getUserOffsetCommands()
        print "cmdList=", cmdList
        for (actor, cmdStr, indList) in cmdList:
            print "actor=%s, cmdStr=%r, indList=%s" % (actor, cmdStr, indList)
            def endFunc(cmdVar, indList=indList):
                for ind in indList:
                    self.itemInfoList[ind].userCorrWdg.clear()
                    self.itemInfoList[ind].userCorrWdg.setEnable(True)
            for ind in indList:
                self.itemInfoList[ind].userCorrWdg.setEnable(False)
            cmdVarList.append(sr.startCmd(actor="tcc", cmdStr=cmdStr, callFunc=endFunc))
        return cmdVarList            

    def _corrCallback(self, keyVar):
        isCurrent=keyVar.isCurrent
        didCorr = keyVar[-1]
        if didCorr == None:
            didCorrStr = "?"
        elif didCorr:
            didCorrStr = "Yes"
        else:
            didCorrStr = "No"

        for ind, itemInfo in enumerate(self.itemInfoList):
            val = keyVar[ind]
            self.itemInfoList[ind].corrWdg.set(val, isCurrent=isCurrent)
            self.itemInfoList[ind].didCorrWdg.set(didCorrStr, isCurrent=isCurrent)

    def _measCallback(self, keyVar):
        isCurrent = keyVar.isCurrent
        for ind, itemInfo in enumerate(self.itemInfoList):
            val = keyVar[ind]
            self.itemInfoList[ind].measWdg.set(val, isCurrent=isCurrent)


class AxisInfo(CategoryInfo):
    def __init__(self, master, row, enableCallFunc, userCallFunc, helpURL):
        CategoryInfo.__init__(self,
            master = master,
            label = "Axes",
            descr = "axes",
            enableCallFunc = enableCallFunc,
            userCallFunc = userCallFunc,
            helpURL = helpURL,
        )
        for ind, labelDescr in enumerate((
            ("RA", "right ascension (angle on sky)"),
            ("Dec", "declination"),
            ("Rot", "rotation"),
        )):
            self._addItem(
                label = labelDescr[0],
                descr = labelDescr[1],
                units = "arcsec",
                precision = 2,
                minValue = -10,
                maxValue =  10,
            )
            isMiddle = (ind == 1)
            self.gridRow(row=row, itemInd=ind, includeEnableWdg=isMiddle)
            row += 1


        guiderModel = TUI.Models.getModel("guider")
        tccModel = TUI.Models.getModel("tcc")

        guiderModel.axisError.addCallback(self._measCallback)
        guiderModel.axisChange.addCallback(self._corrCallback)
        tccModel.objArcOff.addCallback(self._objArcOffCallback)
        tccModel.guideOff.addCallback(self._guideOffset)

    def getUserOffsetCommands(self):
        """Return a list of 0 or more commands to implement the user's requested offsetss
        
        The returned data is a list of tuples, each containing:
        - actor: name of actor
        - cmdStr: command string
        - indList: a list of item indices
        """
        cmdList = []
        raInfo = self.itemInfoList[0]
        decInfo = self.itemInfoList[1]
        if not (raInfo.isClear and decInfo.isClear):
            # correct RA/Dec
            raOffDeg = raInfo.getUserCorr() / RO.PhysConst.ArcSecPerDeg
            decOffDeg = decInfo.getUserCorr() / RO.PhysConst.ArcSecPerDeg
            cmdStr = "offset arc %0.6f, %0.6f" % (raOffDeg, decOffDeg)
            cmdList.append(("tcc", cmdStr, (0, 1)))

        rotInfo = self.itemInfoList[2]
        if not rotInfo.isClear:
            rotOffDeg = rotInfo.getUserCorr() / RO.PhysConst.ArcSecPerDeg
            cmdStr = "offset guide 0.0, 0.0, %0.6f" % (rotOffDeg,)
            cmdList.append(("tcc", cmdStr, (2,)))

        return cmdList

    def _guideOffset(self, keyVar):
        """TCC guider offset callback.
        
        At present only used for rot.
        """
        ii = 2
        guideOff = RO.CnvUtil.posFromPVT(keyVar[ii])
        if guideOff != None:
            guideOff *= 3600.0
        self.itemInfoList[ii].netCorrWdg.set(guideOff, isCurrent=keyVar.isCurrent)

    def _objArcOffCallback(self, keyVar):
        """TCC objArcOff callback
        
        Presently used for RA/Dec correction, but I hope that will switch to guideOff (az/alt).
        """
        for ii in range(2):
            objOff = RO.CnvUtil.posFromPVT(keyVar[ii])
            if objOff != None:
                objOff *= 3600.0
            self.itemInfoList[ii].netCorrWdg.set(objOff, isCurrent=keyVar.isCurrent)


class FocusInfo(CategoryInfo):
    def __init__(self, master, row, enableCallFunc, userCallFunc, helpURL):
        CategoryInfo.__init__(self,
            master = master,
            label = "Focus",
            descr = "secondary focus",
            enableCallFunc = enableCallFunc,
            userCallFunc = userCallFunc,
            helpURL = helpURL,
        )

        self._addItem(
            units = "um",
            precision = 0,
            minValue = -200,
            maxValue =  200,
        )
        self.gridRow(row=row)

        guiderModel = TUI.Models.getModel("guider")
        tccModel = TUI.Models.getModel("tcc")

        guiderModel.focusError.addCallback(self._measCallback)
        guiderModel.focusChange.addCallback(self._corrCallback)
        guiderModel = TUI.Models.getModel("guider")
        tccModel = TUI.Models.getModel("tcc")

        tccModel.secFocus.addCallback(self._secFocusCallback)

    def getUserOffsetCommands(self):
        cmdList = []
        if not self.itemInfoList[0].isClear:
            focusOff = self.itemInfoList[0].getUserCorr()
            cmdStr = "set focus=%0.1f/incremental" % (focusOff,)
            cmdList.append(("tcc", cmdStr, (0,)))
        return cmdList
    
    def _secFocusCallback(self, keyVar):
        """TCC secFocus callback
        """
        self.itemInfoList[0].netCorrWdg.set(keyVar[0], isCurrent=keyVar.isCurrent)


class ScaleInfo(CategoryInfo):
    def __init__(self, master, row, enableCallFunc, userCallFunc, helpURL):
        CategoryInfo.__init__(self,
            master = master,
            label = "Scale",
            descr = "scale ((plate/nominal - 1) * 1e6)",
            enableCallFunc = enableCallFunc,
            userCallFunc = userCallFunc,
            helpURL = helpURL,
        )
        
        self._addItem(
            precision = 1,
            units = "1e6",
            minValue = -20,
            maxValue =  20,
        )
        self.gridRow(row=row)
        
        self.itemInfoList[0].netCorrWdg.helpText = "scale ((plate/nominal - 1) * 1e6); larger is higher resolution"
        
        guiderModel = TUI.Models.getModel("guider")
        tccModel = TUI.Models.getModel("tcc")
        
        guiderModel.scaleError.addCallback(self._measCallback)
        guiderModel.scaleChange.addCallback(self._corrCallback)
        tccModel.scaleFac.addCallback(self._scaleFacCallback)

    def getUserOffsetCommands(self):
        cmdList = []
        if not self.itemInfoList[0].isClear:
            megaScaleOff = self.itemInfoList[0].getUserCorr()
            pctScaleOff = megaScaleOff * 1.0e-4
            cmdStr = "setScale delta=%0.5f" % (pctScaleOff,)
            cmdList.append(("tcc", cmdStr, (0,)))
        return cmdList

    def _corrCallback(self, keyVar):
        """guider scaleChange callback
        
        Display MegaScale = guider percent scale * 1.0e4
        """
        didCorr = keyVar[-1]
        if didCorr == None:
            didCorrStr = "?"
        elif didCorr:
            didCorrStr = "Yes"
        else:
            didCorrStr = "No"

        val = keyVar[0]
        if val != None:
            val *= 1.0e4
        self.itemInfoList[0].corrWdg.set(val, isCurrent=keyVar.isCurrent)
        self.itemInfoList[0].didCorrWdg.set(didCorrStr, isCurrent=keyVar.isCurrent)

    def _measCallback(self, keyVar):
        """guider scaleError callback
        
        Display MegaScale = guider percent scale * 1.0e4
        """
        val = keyVar[0]
        if val != None:
            val *= 1.0e4
        self.itemInfoList[0].measWdg.set(val, isCurrent=keyVar.isCurrent)

    def _scaleFacCallback(self, keyVar):
        """TCC scaleFac callback
        
        Display MegaScale = (scaleFac - 1) * 1e6
        """
        val = keyVar[0]
        if val != None:
            val = (val - 1.0) * 1.0e6
        self.itemInfoList[0].netCorrWdg.set(val, isCurrent=keyVar.isCurrent)


class CorrWdg(Tkinter.Frame):
    def __init__(self, master, doCmdFunc, statusBar=None, helpURL=None):
        """Construct a CorrWdg
        
        Inputs:
        - master: master widget
        - doCmdFunc: a function or method that takes the following arguments:
            cmdStr
            wdg = None
            isGuideOn = False
            actor = None
            abortCmdStr = None
            cmdSummary = None
            failFunc = None
          See GuideWdg.doCmd for more details.
        - statusBar: a status bar
        - helpURL: the help URL for widgets
        """
        Tkinter.Frame.__init__(self, master)
        
        self.doCmdFunc = doCmdFunc
        
        tuiModel = TUI.Models.getModel("tui")
        self.guiderModel = TUI.Models.getModel("guider")

        self.sr = opscore.actor.ScriptRunner(
            name = "ApplyUserCorr",
            runFunc = self._applyRun,
            dispatcher = tuiModel.dispatcher,
            stateFunc = self.enableButtons,
            startNow = False,
            statusBar = statusBar,
            cmdStatusBar = None,
            debug = False,
        )

        self.categoryInfoList = []

        self.applyWdg = RO.Wdg.Button(
            master = self,
            text = "Apply",
            callFunc = self.doApply,
            helpText = "Apply user-supplied correction(s)",
            helpURL = helpURL,
        )
        self.clearWdg = RO.Wdg.Button(
            master = self,
            text = "Clear",
            callFunc = self.doClear,
            helpText = "Clear user-supplied corrections",
            helpURL = helpURL,
        )
        self.cancelWdg = RO.Wdg.Button(
            master = self,
            text = "X",
            callFunc = self.doCancel,
            helpText = "Cancel the Apply command",
            helpURL = helpURL,
        )
        self.enableButtons()
        
        row = 0
        
        self.axisInfo = AxisInfo(
            master = self,
            row = row,
            enableCallFunc = self.doEnableCorrection,
            userCallFunc = self.enableButtons,
            helpURL = helpURL,
        )
        row += self.axisInfo.numItems

        self.focusInfo = FocusInfo(
            master = self,
            row = row,
            enableCallFunc = self.doEnableCorrection,
            userCallFunc = self.enableButtons,
            helpURL = helpURL,
        )
        row += self.focusInfo.numItems

        self.scaleInfo = ScaleInfo(
            master = self,
            row = row,
            enableCallFunc = self.doEnableCorrection,
            userCallFunc = self.enableButtons,
            helpURL = helpURL,
        )
        row += self.scaleInfo.numItems
        
        row = 1
        col = 10
        self.applyWdg.grid(row=row, column=col)
        row += 1
        self.clearWdg.grid(row=row, column=col)
        row += 1
        self.cancelWdg.grid(row=row, column=col)
        row += 1
        
        self.categoryInfoList = [self.axisInfo, self.focusInfo, self.scaleInfo]

    def doApply(self, dum=None):
        """Handle Apply button"""
        self.sr.start()

    def doCancel(self, dum=None):
        """Handle Cancel button"""
        self.sr.cancel()
    
    def doClear(self, dum=None):
        """Handle Clear button"""
        for catInfo in self.categoryInfoList:
            catInfo.clear()

    def doEnableCorrection(self, wdg):
        """Enable or disable the kind of correction named by wdg["text"]
        """
        corrName = wdg["text"].lower()
        if corrName not in ("axes", "focus", "scale"):
            raise RuntimeError("Unknown enable type %s" % (corrName,))
        doEnable = wdg.getBool()
            
        cmdStr = "%s %s" % (corrName, {True: "on", False: "off"}[doEnable])
        self.doCmdFunc(
            cmdStr = cmdStr,
            wdg = wdg,
            cmdSummary = cmdStr,
        )
    
    def enableButtons(self, dum=None):
        """Enable or disable Apply and Current buttons as appropriate.
        """
        isClear = self.isClear
        self.clearWdg.setEnable(not isClear and not self.sr.isExecuting)
        self.applyWdg.setEnable(not self.isClear and not self.sr.isExecuting)
        self.cancelWdg.setEnable(self.sr.isExecuting)

    @property
    def isClear(self):
        """Return True if all user correction widgets are zero or blank.
        """
        for catInfo in self.categoryInfoList:
            if not catInfo.isClear:
                return False
        return True

    def _applyRun(self, sr):
        """Apply corrections as a ScriptRunner script
        
        Works by starting all the commands that are wanted at once,
        then waits for them all to finish
        """
        cmdVarList = []
        for catInfo in self.categoryInfoList:
            cmdVarList += catInfo.startUserOffsetCommands(sr)
        
        yield sr.waitCmdVars(cmdVarList)



if __name__ == "__main__":
    import GuideTest
    #import gc
    #gc.set_debug(gc.DEBUG_SAVEALL) # or gc.DEBUG_LEAK to print lots of messages
    
    def doCmd(
        cmdStr,
        wdg = None,
        isGuideOn = False,
        actor = None,
        abortCmdStr = None,
        cmdSummary = None,
        failFunc = None,
    ):
        print "doCmd(actor=%s, cmdStr=%s)" % (actor, cmdStr)

    root = GuideTest.tuiModel.tkRoot

    testFrame = CorrWdg(root, doCmdFunc=doCmd)
    testFrame.pack(expand="yes", fill="both")
    
    GuideTest.tuiModel.reactor.run()
