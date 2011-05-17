#!/usr/bin/env python
"""APOGEE Calibration Box control and status

History:
2011-05-16 SBeland and ROwen
2011-05-17 ROwen    Overhaul the way calSourceNames is handled.
                    Bug fix: calSourceStatus was mis-handled when the length didn't match calSourceNames.
"""
import itertools
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

        self.shutterWdgSet = self._createWdgSet(
            row = 0,
            name = "Shutter",
            offOnNames = ("Closed", "Open"),
            callFunc = self._doShutter,
            descr = "cal box shutter",
        )
        
        self.calBoxStartRow = 1
        # a dictionary of lamp name: widget set (from _createWdgSet)
        self.calSourceWdgSetDict = RO.Alg.OrderedDict()
        
        self.model = TUI.Models.getModel("apogeecal")

        self.model.calSourceNames.addCallback(self._calSourceNamesCallback)
        self.model.calSourceStatus.addCallback(self._updStatus)
        self.model.calShutter.addCallback(self._updStatus)
        self.model.calBoxController.addCallback(self._updStatus)
        self.showHideWdg.addCallback(self._doShowHide, callNow = True)
        
    def _doShowHide(self, wdg=None):
        """Callback for button to show/hide details
        """
        argDict = {
            self._CalBoxCat: self.showHideWdg.getBool(),
        }
        self.gridder.showHideWdg(**argDict)
    
    def _calSourceNamesCallback(self, wdg):
        """Callback for apogeecal calSourceNames keyword
        """
        newSourceNames = wdg[:]
        if None in newSourceNames or newSourceNames == self.calSourceWdgSetDict.keys():
            return
        
        for wdgSet in self.calSourceWdgSetDict.itervalues():
            for wdg in wdgSet:
                wdg.grid_forget()
        self.calSourceWdgSetDict.clear()
        for ind, sourceName in enumerate(newSourceNames):
            self.calSourceWdgSetDict[str(sourceName)] = self._createWdgSet(
                row = self.calBoxStartRow + ind,
                name = sourceName,
                offOnNames = ("Off", "On"),
                callFunc = self._doLamp,
                descr = "%s lamp" % (sourceName,),
            )
        
        self._updStatus()

    def _createWdgSet(self, row, name, offOnNames, callFunc, descr):
        """Create a set of widgets to control one Cal box item
        
        Inputs:
        - row: row in which to grid widget set
        - name: name of device
        - offOnNames: a pair of names for the off/closed/false and on/open/true state
        - callFunc: a function to call when the user toggles the widget;
            it receives two arguments: name and a RO.Wdg.Checkbutton widget
        - descr: short description; used for help text
        
        Returns two widgets:
        - name label (an RO.Wdg.StrLabel)
        - control widget (an RO.Wdg.Checkbutton)
        """
        def wdgCallFunc(wdg, name=name, callFunc=callFunc):
            callFunc(name, wdg)

        col = 0
        wdgSet = []
        nameWdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = name,
            anchor = "e",
            helpText = descr,
            helpURL = self.helpURL,
        )
        nameWdg.grid(row = row, column = col, sticky="e")
        col += 1
        wdgSet.append(nameWdg)
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
        """Callback for any source control checkbutton
        
        Inputs:
        - name of source
        - checkbutton widget
        """
        if not self._cmdsEnabled:
            return
        wdgStr = btn.getString()
        cmdStr = "source%s source=%s" % (wdgStr, RO.StringUtil.quoteStr(name))
        cmdVar = opscore.actor.keyvar.CmdVar(actor=self.actor, cmdStr=cmdStr)
        self.statusBar.doCmd(cmdVar)
    
    def _doShutter(self, name, btn):
        """Callback for shutter control checkbutton
        
        Inputs:
        - name of shutter (ignored)
        - checkbutton widget
        """
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

            # handle shutter status
            shutterState = self.model.calShutter
            if shutterState == None:
                shutterSeverity = RO.Constants.sevWarning
            else:
                shutterSeverity = RO.Constants.sevNormal
            self.shutterWdgSet[1].setDefault(self.model.calShutter[0])
            self.shutterWdgSet[1].set(self.model.calShutter[0],
                severity = shutterSeverity,
                isCurrent = self.model.calShutter.isCurrent)

    
            # handle source (lamp) status
            lampSeverity = RO.Constants.sevNormal
            if len(self.calSourceWdgSetDict) == len(self.model.calSourceStatus):
                for wdgSet, sourceState in itertools.izip(self.calSourceWdgSetDict.values(), self.model.calSourceStatus):
                    ctrlWdg = wdgSet[1]
                    if sourceState == None:
                        sourceSeverity = RO.Constants.sevWarning
                    else:
                        sourceSeverity = RO.Constants.sevNormal
                    ctrlWdg.set(sourceState,
                        severity = sourceSeverity,
                        isCurrent = self.model.calSourceStatus.isCurrent)
                    ctrlWdg.setDefault(sourceState)

                lampStrList = []
                onLampList = [self.model.calSourceNames[i] for i in range(len(self.model.calSourceStatus))
                    if self.model.calSourceStatus[i]]
                if onLampList:
                    lampStrList.append(", ".join(onLampList) + " on")
                    lampSeverity = RO.Constants.sevWarning
                
                unkLampList = [self.model.calSourceNames[i] for i in range(len(self.model.calSourceStatus))
                    if self.model.calSourceStatus[i] == None]
                if unkLampList:
                    lampStrList.append(", ".join(unkLampList) + " unknown")
                    lampSeverity = RO.Constants.sevWarning
                
                if not lampStrList:
                    lampStr = "lamps off"
                else:
                    lampStr = ", ".join(lampStrList)
            else:
                for wdgSet in self.calSourceWdgSetDict.itervalues():
                    wdgSet[1].setDefault(None, isCurrent=False)
                lampStr = "lamps unknown"
                lampSeverity = RO.Constants.sevWarning
            
            severity = RO.Constants.sevNormal
            
            if self.model.calBoxController[0] == None:
                summaryStr = "Controller state unknown"
                severity = RO.Constants.sevWarning
            elif not self.model.calBoxController[0]:
                summaryStr = "Controller unavailable"
                severity = RO.Constants.sevError
            else:
                shutterSeverity = RO.Constants.sevNormal
                if self.model.calShutter[0] == None:
                    shutterStr = "Shutter unknown"
                    shutterSeverity = RO.Constants.sevWarning
                elif self.model.calShutter[0]:
                    shutterStr = "Open"
                    shutterSeverity = RO.Constants.sevWarning
                else:
                    shutterStr = "Closed"

                # lamps were handled above, where we made sure there were the expected number of status items

                summaryStr = "%s; %s" % (shutterStr, lampStr)
                severity = max(shutterSeverity, lampSeverity)
    
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
