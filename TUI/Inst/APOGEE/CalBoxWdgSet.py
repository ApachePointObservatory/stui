#!/usr/bin/env python
"""APOGEE Calibration Box control and status

History:
2011-05-14 SBeland and ROwen
"""
import Tkinter
import RO.Constants
import RO.Wdg
import RO.TkUtil
import RO.StringUtil
import TUI.Base.Wdg
import TUI.Models
import TUI.Misc
from TUI.Misc.MCP import BipolarDeviceWdg
import opscore.actor.keyvar
import LimitParser

class CalBoxWdgSet(object):
    _CalBoxCat = "calbox"
    def __init__(self, gridder, statusBar, colSpan=3, helpURL=None):
        """Create a CalBoxWdgSet
        
        Inputs:
        - gridder: an instance of RO.Wdg.Gridder;
            the widgets are gridded starting at the next row and default column
        - colSpan: the number of columns to span
        - helpURL: path to an HTML help file or None
        
        Note: you may wish to call master.columnconfigure(n, weight=1)
        where n is the last column of this widget set
        so that the parent widget can fill available space
        without resizing the columns of other contained widgets.
        """
        self.helpURL = helpURL
        self.statusBar = statusBar
        self.actor = "apogeecal"
        self.starting = True
        self._cmdsEnabled = True
        
        self.gridder = gridder
        master = self.gridder._master
        
        self.model = TUI.Models.getModel("apogeecal")

        self.showHideWdg = RO.Wdg.Checkbutton(
            master = master,
            text = "Cal Box",
            indicatoron = False,
            callFunc = self._doShowHide,
            helpText = "Show/hide calibration box controls.",
            helpURL = helpURL,
        )
        
        self.summaryWdg = RO.Wdg.StrLabel(
            master = master,
            anchor = "w",
            helpText = "Calibration box status summary",
            helpURL = helpURL,
        )
        gridder.gridWdg(self.showHideWdg, self.summaryWdg, sticky="w", colSpan=colSpan-1)
        
        # hidable frame showing the controls

        self.detailWdg = Tkinter.Frame(
            master = master,
            borderwidth = 1,
            relief = "solid",
        )
        self.gridder.gridWdg(False, self.detailWdg, colSpan=colSpan, sticky="w", cat=self._CalBoxCat)

        self.shutterWdgSet = self.createWdgSet(
            row = 0,
            name = "Shutter",
            offOnNames = ("Closed", "Open"),
            callFunc = self._doShutter,
            descr = "cal box shutter",
        )
        
        self.calBoxStartRow = 1
        self.calSourceNames = ()
        # a list of (lamp name, checkbutton)
        self.calSourceWdgSet = []
        
        self.model = TUI.Models.getModel("apogeecal")

        self.model.calSourceNames.addCallback(self._calSourceNamesCallback)
        self.model.calSourceStatus.addCallback(self._updStatus)
        self.model.calShutter.addCallback(self._updStatus)
        self.model.calBoxController.addCallback(self._updStatus)
        self.showHideWdg.addCallback(self._doShowHide, callNow = True)
        
    def _doShowHide(self, wdg=None):
        argDict = {
            self._CalBoxCat: self.showHideWdg.getBool(),
        }
        self.gridder.showHideWdg(**argDict)
    
    def _calSourceNamesCallback(self, wdg):
        if None in wdg or tuple(wdg[:]) == self.calSourceNames:
            return
        
        for wdgSet in self.calSourceWdgSet:
            for wdg in wdgSet:
                wdg.grid_forget()
        self.calSourceWdgSet = []
        for ind, sourceName in enumerate(wdg):
            self.calSourceWdgSet.append(self.createWdgSet(
                row = self.calBoxStartRow + ind,
                name = sourceName,
                offOnNames = ("Off", "On"),
                callFunc = self._doLamp,
                descr = "%s lamp" % (sourceName,),
            ))

    def createWdgSet(self, row, name, offOnNames, callFunc, descr):
        """Create a set of widgets to control one Cal box item
        
        Inputs:
        - row: row in which to grid widget set
        - name: name of device
        - offOnNames: a pair of names for the off/closed/false and on/open/true state
        - callFunc: a function to call when the user toggles the widget;
            it receives two arguments: name and a RO.Wdg.Checkbutton widget
        - descr: short description; used for help text
        """
        def wdgCallFunc(wdg, name=name, callFunc=callFunc):
            callFunc(name, wdg)

        col = 0
        wdgSet = []
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = name,
            anchor = "e",
            helpText = descr,
            helpURL = self.helpURL,
        )
        wdg.grid(row = row, column = col, sticky="e")
        col += 1
        wdgSet.append(wdg)
        btn = RO.Wdg.Checkbutton (
            master = self.detailWdg,
            offvalue = offOnNames[0],
            onvalue = offOnNames[1],
            defValue = offOnNames[0],
            showValue = True,
            indicatoron = True,
            anchor = "w",
            callFunc = wdgCallFunc,
            autoIsCurrent = True,
            helpText = "press to toggle %s" % (descr,),
            helpURL = self.helpURL,
        )
        wdgSet.append(btn)
        btn.grid(row = row, column = col, sticky="w")
        col += 1
        return wdgSet
        
    def _doLamp(self, name, btn):
        if not self._cmdsEnabled:
            return
        wdgStr = btn.getString()
        cmdStr = "source%s source=%s" % (wdgStr, RO.StringUtil.quoteStr(name))
        cmdVar = opscore.actor.keyvar.CmdVar(actor=self.actor, cmdStr=cmdStr)
        self.statusBar.doCmd(cmdVar)
    
    def _doShutter(self, name, btn):
        if not self._cmdsEnabled:
            return
        wdgStr = btn.getString()
        cmdStr = "shutter%s" % (wdgStr,)
        cmdVar = opscore.actor.keyvar.CmdVar(actor=self.actor, cmdStr=cmdStr)
        self.statusBar.doCmd(cmdVar)

    def _updStatus(self, *dumArgs):
        """Update status
        """
        try:
            self._cmdsEnabled = False

            self.shutterWdgSet[1].setDefault(self.model.calShutter, isCurrent=self.model.calShutter.isCurrent)
    
            if len(self.calSourceWdgSet) == len(self.model.calSourceStatus):
                for i, sourceState in enumerate(self.model.calSourceStatus):
                    self.calSourceWdgSet[i][1].setDefault(sourceState, isCurrent=self.model.calSourceStatus.isCurrent)
                else:
                    for wdgSet in self.calSourceWdgSet:
                        wdgSet[1].setDefault(None, isCurrent=self.model.calSourceStatus.isCurrent)
            
            severity = RO.Constants.sevNormal
            
            if self.model.calBoxController[0] == None:
                summaryStr = "Controller state unknown"
                severity = RO.Constants.sevWarning
            elif not self.model.calBoxController[0]:
                summaryStr = "Controller unavailable"
                severity = RO.Constants.sevError
            else:
                if self.model.calShutter[0] == None:
                    shutterStr = "Shutter unknown"
                    severity = RO.Constants.sevWarning
                elif self.model.calShutter[0]:
                    shutterStr = "Open"
                    severity = RO.Constants.sevWarning
                else:
                    shutterStr = "Closed"
                
                lampStrList = []
                onLampList = [self.model.calSourceNames[i] for i in range(len(self.model.calSourceStatus))
                    if self.model.calSourceStatus[i]]
                if onLampList:
                    lampStrList.append(", ".join(onLampList) + " on")
                    severity = max(severity, RO.Constants.sevWarning)
                
                unkLampList = [self.model.calSourceNames[i] for i in range(len(self.model.calSourceStatus))
                    if self.model.calSourceStatus[i] == None]
                if unkLampList:
                    lampStrList.append(", ".join(unkLampList) + " unknown")
                    severity = max(severity, RO.Constants.sevWarning)
                
                if not lampStrList:
                    lampStr = "lamps off"
                else:
                    lampStr = ", ".join(lampStrList)
                
                summaryStr = "%s; %s" % (shutterStr, lampStr)
    
            isCurrent = self.model.calBoxController.isCurrent and \
                self.model.calShutter.isCurrent and self.model.calSourceStatus.isCurrent
            self.summaryWdg.set(summaryStr, isCurrent=isCurrent, severity=severity)            
        finally:
            self._cmdsEnabled = True

if __name__ == "__main__":
    import TestData
    import TUI.Base.Wdg
    
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot

    statusBar = TUI.Base.Wdg.StatusBar(root)

    testFrame = Tkinter.Frame(root)
    gridder = RO.Wdg.Gridder(testFrame)
    CalBoxWdgSet = CalBoxWdgSet(gridder, statusBar)
    testFrame.pack(side="top", expand=True)
    testFrame.columnconfigure(2, weight=1)

    statusBar.pack(side="top", expand=True, fill="x")

    TestData.start()

    tuiModel.reactor.run()
