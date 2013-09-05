#!/usr/bin/env python
"""APOGEE Calibration Box control and status

History:
2011-05-16 SBeland and ROwen
2011-05-17 ROwen    Overhaul the way calSourceNames is handled.
                    Bug fix: calSourceStatus was mis-handled when the length didn't match calSourceNames.
2011-08-16 ROwen    Document statusBar parameter
2011-09-01 ROwen    Added support for cancelling commands.
                    Modified to use BaseDeviceWdg and to look more like ShutterWdgSet.
2012-11-14 ROwen    Stop using Checkbutton indicatoron=False; it is no longer supported on MacOS X.
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
import BaseDeviceWdg

class CalBoxWdgSet(object):
    """Widgets to control APOGEE's calibration box
    """
    _CalBoxCat = "calbox"
    def __init__(self, gridder, statusBar, colSpan=3, helpURL=None):
        """Create a CalBoxWdgSet
        
        Inputs:
        - gridder: an instance of RO.Wdg.Gridder;
            the widgets are gridded starting at the next row and default column
        - statusBar: status bar (to send commands)
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
            callFunc = self._doShowHide,
            helpText = "Show calibration box controls?",
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
        
        detailGridder = RO.Wdg.Gridder(master=self.detailWdg, sticky="w")

        self.shutterWdg = _ShutterWdg(
            master = self.detailWdg,
            statusBar = self.statusBar,
            helpURL = helpURL,
        )
        detailGridder.gridWdg("Shutter", self.shutterWdg)
        
        self.sourcesWdg = _SourcesWdg(
            master = self.detailWdg,
            statusBar = self.statusBar,
            helpURL = helpURL,
        )
        detailGridder.gridWdg("Sources", self.sourcesWdg)
        
        self.model = TUI.Models.getModel("apogeecal")

        self.model.calBoxController.addCallback(self.updateStatus)
        self.model.calShutter.addCallback(self.updateStatus)
        self.model.calSourceStatus.addCallback(self.updateStatus)
        self.model.calSourceNames.addCallback(self.updateStatus)
        self.showHideWdg.addCallback(self._doShowHide, callNow = True)
        
    def _doShowHide(self, wdg=None):
        """Callback for button to show/hide details
        """
        argDict = {
            self._CalBoxCat: self.showHideWdg.getBool(),
        }
        self.gridder.showHideWdg(**argDict)

    def updateStatus(self, *dumArgs):
        """Update status
        """
        isCurrent = self.model.calBoxController.isCurrent \
            and self.model.calShutter.isCurrent \
            and self.model.calSourceStatus.isCurrent \
            and self.model.calSourceNames.isCurrent
            
        if self.model.calBoxController[0] == None:
            summaryStr = "Controller state unknown"
            severity = RO.Constants.sevWarning
        elif not self.model.calBoxController[0]:
            summaryStr = "Controller unavailable"
            severity = RO.Constants.sevError
        else:
            shutterStr, shutterSeverity = self.shutterWdg.getSummary()
            sourceStr, sourceSeverity = self.sourcesWdg.getSummary()
            
            summaryStr = "%s; %s" % (shutterStr, sourceStr)
            severity = max(shutterSeverity, sourceSeverity)
        self.summaryWdg.set(summaryStr, isCurrent=isCurrent, severity=severity)            

class _SourcesWdg(BaseDeviceWdg.BaseDeviceWdg):
    """Widget to control cal box sources (lamps)
    """
    def __init__(self, master, statusBar, helpURL=None):
        BaseDeviceWdg.BaseDeviceWdg.__init__(self,
            master = master,
            actor = "apogeecal",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        
        self.sourceWdgFrame = Tkinter.Frame(self)
        self.sourceWdgFrame.pack(side="left")

        self.cancelBtn.pack(side="left")
        
        # a dictionary of source name: widget set (from _createWdgSet)
        self.wdgDict = RO.Alg.OrderedDict()

        self.model = TUI.Models.getModel(self.actor)
        self.model.calSourceStatus.addCallback(self.updateStatus)

        self.model.calSourceNames.addCallback(self._calSourceNamesCallback)
        self.model.calSourceStatus.addCallback(self.updateStatus)
    
    def _calSourceNamesCallback(self, keyVar):
        """Callback for apogeecal calSourceNames keyword
        """
        newSourceNames = keyVar[:]
        if (None in newSourceNames) or (newSourceNames == self.wdgDict.keys()):
            return
        
        for wdg in self.wdgDict.itervalues():
            wdg.pack_forget()
        self.wdgDict.clear()
        for sourceName in newSourceNames:
            wdg = RO.Wdg.Checkbutton (
                master = self.sourceWdgFrame,
                text = sourceName,
                defValue = False,
                anchor = "w",
                callFunc = self._doSource,
                autoIsCurrent = True,
                helpText = "Toggle %s source" % (sourceName,),
                helpURL = self.helpURL,
            )
            self.wdgDict[str(sourceName)] = wdg
            wdg.pack(side="left")
        
        self.updateStatus()

    def _doSource(self, wdg):
        """Callback for any source control checkbutton
        
        Inputs:
        - checkbutton widget; its text property must be the name of the source
        """
        name = wdg["text"]
        if wdg.getBool():
            desState = "On"
        else:
            desState = "Off"
        cmdStr = "source%s source=%s" % (desState, RO.StringUtil.quoteStr(name))
        self.doCmd(cmdStr)

    def enableButtons(self, dumCmd=None):
        """Enable or disable widgets, as appropriate
        """
        isRunning = self.isRunning
        for wdg in self.wdgDict.itervalues():
            wdg.setEnable(not isRunning)
        self.cancelBtn.setEnable(isRunning)
    
    def getSummary(self):
        """Return a string, severity summarizing the state of the sources
        """
        severity = RO.Constants.sevWarning
        if len(self.wdgDict) == len(self.model.calSourceStatus):
            sourceStrList = []
            onSourceList = [self.model.calSourceNames[i] for i in range(len(self.model.calSourceStatus))
                if self.model.calSourceStatus[i]]
            if onSourceList:
                sourceStrList.append(", ".join(onSourceList) + " ON")
            
            unkSourceList = [self.model.calSourceNames[i] for i in range(len(self.model.calSourceStatus))
                if self.model.calSourceStatus[i] == None]
            if unkSourceList:
                sourceStrList.append(", ".join(unkSourceList) + " ???")
            
            if not sourceStrList:
                sumStr = "Sources off"
                severity = RO.Constants.sevNormal
            else:
                sumStr = "; ".join(sourceStrList)
        else:
            sumStr = "Sources ???"

        return sumStr, severity

    def updateStatus(self, *dumArgs):
        """Update widget status
        """
        with self.updateLock():
            # handle source (lamp) status
            severity = RO.Constants.sevNormal
            if len(self.wdgDict) == len(self.model.calSourceStatus):
                for wdg, sourceState in itertools.izip(self.wdgDict.values(), self.model.calSourceStatus):
                    if sourceState == None:
                        sourceSeverity = RO.Constants.sevWarning
                    else:
                        sourceSeverity = RO.Constants.sevNormal
                    wdg.setDefault(sourceState)
                    wdg.set(sourceState,
                        severity = sourceSeverity,
                        isCurrent = self.model.calSourceStatus.isCurrent)
            else:
                for wdg in self.wdgDict.itervalues():
                    wdg.setDefault(None, isCurrent=False)
                severity = RO.Constants.sevWarning


class _ShutterWdg(BaseDeviceWdg.BaseDeviceWdg):
    """A widget to open or close the cold shutter
    """
    def __init__(self, master, statusBar, helpURL=None):
        BaseDeviceWdg.BaseDeviceWdg.__init__(self,
            master = master,
            actor = "apogeecal",
            statusBar = statusBar,
            helpURL = helpURL,
        )

        self.shutterWdg = RO.Wdg.Checkbutton(
            master = self,
            onvalue = "Open",
            offvalue = "Closed",
            showValue = True,
            callFunc = self._doShutter,
            helpText = "Open or close cold shutter",
            helpURL = helpURL,
        )
        self.shutterWdg.pack(side="left")

        self.cancelBtn.pack(side="left")

        self.model = TUI.Models.getModel(self.actor)
        self.model.calShutter.addCallback(self.updateStatus)

    def _doShutter(self, wdg=None):
        """Send a command to open or close the shutter
        """
        doOpen = self.shutterWdg.getBool()
        if doOpen:
            cmdStr = "shutterOpen"
        else:
            cmdStr = "shutterClose"
        self.doCmd(cmdStr)

    def enableButtons(self, dumCmd=None):
        """Enable or disable widgets, as appropriate
        """
        isRunning = self.isRunning
        self.shutterWdg.setEnable(not isRunning)
        self.cancelBtn.setEnable(isRunning)

    def getSummary(self):
        """Return a string and severity summarizing the current state
        """
        isOpen = self.model.calShutter[0]
        isCurrent = self.model.calShutter.isCurrent
        severity = RO.Constants.sevNormal

        if isOpen == None:
            sumStr = "?"
            severity = RO.Constants.sevWarning
        elif isOpen:
            sumStr = "Open"
        else:
            sumStr = "Closed"

        return sumStr, severity

    def updateStatus(self, keyVar=None):
        """shutterLimitSwitch keyword callback
        """
        isOpen = self.model.calShutter[0]
        isCurrent = self.model.calShutter.isCurrent

        with self.updateLock():
            if isOpen == None:
                self.shutterWdg.setIsCurrent(False)
            else:
                self.shutterWdg.set(isOpen, isCurrent=isCurrent)

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
