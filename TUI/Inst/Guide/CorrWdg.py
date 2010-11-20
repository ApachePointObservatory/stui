#!/usr/bin/env python
"""Correction widgets

These show the measured error and proposed correction from the guider,
control whether automatic correction is enabled
and allow the user to specify an additional correction.

History:
2010-11-19 ROwen    Extracted from GuideWdg and overhauled.
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
    def __init__(self, master, label, descr, units, measKey=None, corrKey=None, keyInd=0, callFunc=None,
        defFormat="%0.2f", minValue=None, maxValue=None, helpURL=None):
        """Create an ItemInfo
        
        Inputs:
        - master: master widget
        - label: label for title widget
        - descr: short description for help string
        - units: units of this item
        - measKey: a guider keyVar that contains the measured error; None if you want to set measWdg yourself
        - corrKey: a guider keyVar that contains the correction to be applied; None if you want to set corrWdg yourself
        - keyInd: index of keyVar for this item
        - callFunc: a function to call when userCorrWdg is modified
        - defFormat: default format for display of the values
        - minValue: minimum value for userCorrWdg
        - maxValue: maximum value for userCorrWdg
        - helpURL: help URL
        """
        self.label = label
        self.descr = descr
        self.units = units
        self.measWdg = RO.Wdg.FloatEntry(
            master = master,
            defFormat = defFormat,
            readOnly = True,
            width = self.WdgWidth,
            helpText = "measured %s error" % (self.descr,),
            helpURL = helpURL,
        )
        self.corrWdg = RO.Wdg.FloatEntry(
            master = master,
            defFormat = defFormat,
            readOnly = True,
            width = self.WdgWidth,
            helpText = "%s correction from guider" % (self.descr,),
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
            helpText = "%s user-supplied correction" % (self.descr,),
            helpURL = helpURL,
        )
        if measKey:
            measKey.addValueCallback(self.measWdg.set, ind=keyInd)
        if corrKey:
            corrKey.addValueCallback(self.corrWdg.set, ind=keyInd)

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
    
    Categories are axes, focus or scale
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

    def addItem(self, units, measKey, corrKey, keyInd=0, label=None, descr=None, defFormat="%0.2f", minValue=None, maxValue=None):
        """Add an item

        Inputs:
        - units: units of this item
        - measKey: a guider keyVar that contains the measured error
        - corrKey: a guider keyVar that contains the correction to be applied
        - keyInd: index of keyVar for this item
        - label: label for title widget; defaults to None
        - descr: short description for help string; defaults to category descr
        - defFormat: default format for display of the values
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
            measKey = measKey,
            corrKey = corrKey,
            keyInd = keyInd,
            defFormat = defFormat,
            minValue = minValue,
            maxValue = maxValue,
            helpURL = self.helpURL,
        ))
    
    def clear(self):
        for itemInfo in self.itemInfoList:
            itemInfo.clear()

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
        
        self.itemInfoList[itemInd].measWdg.grid(row=row, column=col)
        col += 1
        self.itemInfoList[itemInd].corrWdg.grid(row=row, column=col)
        col += 1
        self.itemInfoList[itemInd].userCorrWdg.grid(row=row, column=col)
        col += 1
        unitsLabel = RO.Wdg.StrLabel(master=self.master, text=self.itemInfoList[itemInd].units)
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
        self.settingCorrEnableWdg = False
        
        tuiModel = TUI.Models.getModel("tui")
        self.tccModel = TUI.Models.getModel("tcc")
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
        
        self.axesInfo = CategoryInfo(
            master = self,
            label = "Axes",
            descr = "axes",
            enableCallFunc = self.doEnableCorrection,
            userCallFunc = self.enableButtons,
            helpURL = helpURL,
        )
        for ind, labelDescr in enumerate((
            ("RA", "right ascension (angle on sky)"),
            ("Dec", "declination"),
            ("Rot", "rotation"),
        )):
            self.axesInfo.addItem(
                label = labelDescr[0],
                descr = labelDescr[1],
                units = "arcsec",
                measKey = self.guiderModel.axisError,
                corrKey = self.guiderModel.axisChange,
                keyInd = ind,
                defFormat = "%0.2f",
                minValue = -10,
                maxValue =  10,
            )
            isMiddle = (ind == 1)
            self.axesInfo.gridRow(row=row, itemInd=ind, includeEnableWdg=isMiddle)
            row += 1

        self.focusInfo = CategoryInfo(
            master = self,
            label = "Focus",
            descr = "secondary focus",
            enableCallFunc = self.doEnableCorrection,
            userCallFunc = self.enableButtons,
            helpURL = helpURL,
        )
        self.focusInfo.addItem(
            units = "um",
            measKey = self.guiderModel.focusError,
            corrKey = self.guiderModel.focusChange,
            defFormat = "%0.0f",
            minValue = -200,
            maxValue =  200,
        )
        self.focusInfo.gridRow(row=row)
        row += 1

        self.scaleInfo = CategoryInfo(
            master = self,
            label = "Scale",
            descr = "plate scale",
            enableCallFunc = self.doEnableCorrection,
            userCallFunc = self.enableButtons,
            helpURL = helpURL,
        )
        self.scaleInfo.addItem(
            units = "%",
            measKey = self.guiderModel.scaleError,
            corrKey = self.guiderModel.scaleChange,
            defFormat = "%0.4f",
            minValue = -0.002,
            maxValue =  0.002,
        )
        self.scaleInfo.gridRow(row=row)
        row += 1
        
        self.guiderModel.scaleError.addCallback(self._scaleErrorCallback)
        self.guiderModel.scaleChange.addCallback(self._scaleChangeCallback)
        
        row = 1
        col = 10
        self.applyWdg.grid(row=row, column=col)
        row += 1
        self.clearWdg.grid(row=row, column=col)
        row += 1
        self.cancelWdg.grid(row=row, column=col)
        row += 1
        
        self.categoryInfoList = [self.axesInfo, self.focusInfo, self.scaleInfo]
        
        self.guiderModel.guideEnable.addCallback(self.guideEnableCallback)

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
        """Enable or disable some the kind of correction named by wdg["text"]
        """
        if self.settingCorrEnableWdg:
            return
            
        corrName = wdg["text"].lower()
        if corrName not in ("axes", "focus", "scale"):
            raise RuntimeError("Unknown enable type %s" % (corrName,))
        doEnable = wdg.getBool()
            
        cmdStr = "%s %s" % (corrName, {True: "on", False: "off"}[doEnable])
        self.doCmdFunc(
            cmdStr = cmdStr,
            wdg = wdg,
            cmdSummary = cmdStr,
            failFunc = self.guideEnableCallback,
        )
    
    def enableButtons(self, dum=None):
        """Enable or disable Apply and Current buttons as appropriate.
        """
        isClear = self.isClear
        self.clearWdg.setEnable(not isClear and not self.sr.isExecuting)
        self.applyWdg.setEnable(not self.isClear and not self.sr.isExecuting)
        self.cancelWdg.setEnable(self.sr.isExecuting)

    def guideEnableCallback(self, dum=None):
        """Callback for guider.guideEnable
        """
        keyVar = self.guiderModel.guideEnable
        isCurrent = keyVar.isCurrent
        try:
            self.settingCorrEnableWdg = True
            for ind, catInfo in enumerate(self.categoryInfoList):
                catInfo.enableWdg.setBool(keyVar[ind], isCurrent)
                for itemInfo in catInfo.itemInfoList:
                    if keyVar[ind]:
                        itemInfo.userCorrWdg.helpText = "%s correction applied by guider" % (itemInfo.descr,)
                    else:
                        itemInfo.userCorrWdg.helpText = "%s correction suggested by guider" % (itemInfo.descr,)
        finally:
            self.settingCorrEnableWdg = False

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
        
        raInfo = self.axesInfo.itemInfoList[0]
        decInfo = self.axesInfo.itemInfoList[1]
        if not (raInfo.isClear and decInfo.isClear):
            # correct RA/Dec
            raOffDeg = raInfo.getUserCorr() / RO.PhysConst.ArcSecPerDeg
            decOffDeg = decInfo.getUserCorr() / RO.PhysConst.ArcSecPerDeg
            cmdStr = "offset arc %0.6f, %0.6f" % (raOffDeg, decOffDeg)
            self.axesInfo.itemInfoList[0].userCorrWdg.setEnable(False)
            self.axesInfo.itemInfoList[1].userCorrWdg.setEnable(False)
            def endFunc(cmdVar):
                self.axesInfo.itemInfoList[0].clear()
                self.axesInfo.itemInfoList[0].userCorrWdg.setEnable(True)
                self.axesInfo.itemInfoList[1].clear()
                self.axesInfo.itemInfoList[1].userCorrWdg.setEnable(True)
            cmdVarList.append(sr.startCmd(actor="tcc", cmdStr=cmdStr, callFunc=endFunc))

        rotInfo = self.axesInfo.itemInfoList[2]
        if not rotInfo.isClear:
            rotOffDeg = rotInfo.getUserCorr() / RO.PhysConst.ArcSecPerDeg
            cmdStr = "offset guide 0.0, 0.0, %0.6f" % (rotOffDeg,)
            self.axesInfo.itemInfoList[2].userCorrWdg.setEnable(False)
            def endFunc(cmdVar):
                self.axesInfo.itemInfoList[2].clear()
                self.axesInfo.itemInfoList[2].userCorrWdg.setEnable(True)
            cmdVarList.append(sr.startCmd(actor="tcc", cmdStr=cmdStr, callFunc=endFunc))

        if not self.focusInfo.itemInfoList[0].isClear:
            focusOff = self.focusInfo.itemInfoList[0].getUserCorr()
            cmdStr = "set focus=%0.1f/incremental" % (focusOff,)
            self.focusInfo.itemInfoList[0].userCorrWdg.setEnable(False)
            def endFunc(cmdVar):
                self.focusInfo.itemInfoList[0].clear()
                self.focusInfo.itemInfoList[0].userCorrWdg.setEnable(True)
            cmdVarList.append(sr.startCmd(actor="tcc", cmdStr=cmdStr, callFunc=endFunc))
            
        if not self.scaleInfo.itemInfoList[0].isClear:
            scaleOff = self.scaleInfo.itemInfoList[0].getUserCorr()
            cmdStr = "setScale delta=%0.1f" % (scaleOff,)
            self.scaleInfo.itemInfoList[0].userCorrWdg.setEnable(False)
            def endFunc(cmdVar):
                self.scaleInfo.itemInfoList[0].clear()
                self.scaleInfo.itemInfoList[0].userCorrWdg.setEnable(True)
            cmdVarList.append(sr.startCmd(actor="guider", cmdStr=cmdStr, callFunc=endFunc))
        
        yield sr.waitCmdVars(cmdVarList)

    def _scaleErrorCallback(self, keyVar):
        """guider.scaleError keyVar callback
        
        Needed because it is reported as a fraction but display and command use percent
        """
        scaleErr = keyVar[0]
        if scaleErr != None:
            scaleErr *= 100.0
        self.scaleInfo.itemInfoList[0].measWdg.set(scaleErr, isCurrent=keyVar.isCurrent)

    def _scaleChangeCallback(self, keyVar):
        """guider.scaleChange keyVar callback
        
        Needed because it is reported as a fraction but display and command use percent
        """
        scaleCorr = keyVar[0]
        if scaleCorr != None:
            scaleCorr *= 100.0
        self.scaleInfo.itemInfoList[0].corrWdg.set(scaleCorr, isCurrent=keyVar.isCurrent)


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
