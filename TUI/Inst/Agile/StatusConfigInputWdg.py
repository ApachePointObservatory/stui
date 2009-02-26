#!/usr/bin/env python
"""Configuration input panel for Agile.

To do:
- Filter wheel support.

History:
2008-10-24 ROwen    preliminary adaptation from DIS
2008-11-06 ROwen    Removed unused detector controls; the rest is not yet functional
2008-11-07 ROwen    Implemented temperature display. Still need functional filter control.
2008-11-10 ROwen    Commented out nonfunctional filter code.
                    Set minimum temperature width so no info shows up properly.
                    Call temperature callbacks right away.
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import TUI.TUIModel
import AgileModel

_DataWidth = 8  # width of data columns
_EnvWidth = 6 # width of environment value columns

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
    InstName = "Agile"
    HelpPrefix = "Instruments/%sWin.html#" % (InstName,)

    # category names
    ConfigCat = RO.Wdg.StatusConfigGridder.ConfigCat
    TempCat = 'temp'

    def __init__(self,
        master,
    **kargs):
        """Create a new widget to show status for and configure Agile
        """
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        self.model = AgileModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()
        
        self.settingCurrWin = False
    
        gr = RO.Wdg.StatusConfigGridder(
            master = self,
            sticky = "w",
            numStatusCols = 3,
        )
        self.gridder = gr
        
        # filter (plus blank label to maintain minimum width)
        blankLabel = Tkinter.Label(self, width=_DataWidth)

        self.filterCurrWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "current filter",
            helpURL = self.HelpPrefix + "Filter",
        )
        
        self.filterTimerWdg = RO.Wdg.TimeBar(master = self, valueFormat = "%3.0f")
        
        self.filterUserWdg = RO.Wdg.OptionMenu(
            master = self,
            items=[],
            helpText = "requested filter",
            helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
            isCurrent = False,
        )

#         filtRow = gr.getNextRow()
#         # reserve _DataWidth width
#         blankLabel.grid(
#             row = filtRow,
#             column = 1,
#             columnspan = 2,
#         )
#         gr.gridWdg (
#             label = 'Filter',
#             dataWdg = self.filterCurrWdg,
#             units = None,
#             cfgWdg = self.filterUserWdg,
#             colSpan = 2,
#         )
#         self.filterTimerWdg.grid(
#             row = filtRow,
#             column = 1,
#             columnspan = 2,
#             sticky = "w",
#         )
        self._showFilterTimer(False)

#         self.model.filter.addIndexedCallback(self._updFilter)
#         self.model.filterTime.addIndexedCallback(self._updFilterTime)

        # Temperature State information
        
        self.ccdTempStateDict = {
            None: (None, RO.Constants.sevNormal),
            "normal": ("", RO.Constants.sevNormal),
            "low": ("Low", RO.Constants.sevWarning),
            "high": ("High", RO.Constants.sevWarning),
            "verylow": ("Very Low", RO.Constants.sevError),
            "veryhigh": ("Very High", RO.Constants.sevError),
        }
        
        # Camera connected
        self.cameraConnStateWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "Camera connection state",
            helpURL = self.HelpPrefix + "CameraConn",
        )
        gr.gridWdg("Camera", self.cameraConnStateWdg)
        
        # CCD Temperature
        
        self.tempShowHideWdg = RO.Wdg.Checkbutton(
            master = self,
            text = "CCD Temp",
            indicatoron = False,
            helpText = "Show/hide temperature details",
            helpURL = self.HelpPrefix + "CCDTemp",
        )
        
        self.ccdTempWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 1,
            width = _EnvWidth,
            helpText = "Current CCD Temp (C)",
            helpURL = self.HelpPrefix + "CCDTemp",
        )
        
        self.ccdTempStateWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "Is temperature OK?",
            helpURL = self.HelpPrefix + "CCDTemp",
        )

        gr.gridWdg (
            label = self.tempShowHideWdg,
            dataWdg = (self.ccdTempWdg, self.ccdTempStateWdg),
        )
        
        # CCD Set Temperature
        
        self.ccdSetTempWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 1,
            width = _EnvWidth,
            helpText = "Desired CCD Temp (C)",
            helpURL = self.HelpPrefix + "CCDTemp",
        )
        
        self.ccdSetTempStateWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "Is desired temperature OK?",
            helpURL = self.HelpPrefix + "CCDTemp",
        )

        gr.gridWdg (
            label = "CCD Set Temp",
            dataWdg = (self.ccdSetTempWdg, self.ccdSetTempStateWdg),
            cat = self.TempCat,
        )
        
        # CCD Temperature Limits
        
        tempLimitsLabels = ("Low", "High", "Very Low", "Very High")
        self.ccdTempLimitsFrame = Tkinter.Frame(self)
        self.ccdTempLimitsWdgDict = RO.Alg.OrderedDict()
        col = 0
        for label in tempLimitsLabels:
            labelWdg = RO.Wdg.StrLabel(
                self.ccdTempLimitsFrame,
                text = label,
            )
            valueWdg = RO.Wdg.FloatLabel(
                self.ccdTempLimitsFrame,
                precision = 1,
                width = _EnvWidth,
                helpText = "Error limit for %s CCD temp." % (label.lower(),)
            )
            labelWdg.grid(row=0, column=col)
            valueWdg.grid(row=1, column=col)
            col += 1
            self.ccdTempLimitsWdgDict[label] = (labelWdg, valueWdg)
        
        gr.gridWdg(
            label = "CCD Temp Limits",
            dataWdg = self.ccdTempLimitsFrame,
            colSpan = 10,
            numStatusCols = None,
            cat = self.TempCat,
        )
        
        gr.allGridded()
        
        # add callbacks that deal with multiple widgets
#         self.model.filterNames.addCallback(self._updFilterNames)
        self.tempShowHideWdg.addCallback(self._doShowHide, callNow = False)
        self.model.ccdTemp.addCallback(self._updCCDTemp, callNow = True)
        self.model.ccdSetTemp.addCallback(self._updCCDSetTemp, callNow = True)
        self.model.ccdTempLimits.addCallback(self._updTempLimits, callNow = True)
        self.model.cameraConnState.addCallback(self._updCameraConnState, callNow = True)
        self._doShowHide()
        
        eqFmtFunc = RO.InputCont.BasicFmt(
            nameSep="=",
        )

        # set up the input container set
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = 'filters set',
                    wdgs = self.filterUserWdg,
                    formatFunc = eqFmtFunc,
                ),
            ],
        )
        
        def repaint(evt):
            self.restoreDefault()
        self.bind('<Map>', repaint)

    def _doShowHide(self, wdg=None):
        showTemps = self.tempShowHideWdg.getBool()
        argDict = {self.TempCat: showTemps}
        self.gridder.showHideWdg (**argDict)
    
    def _showFilterTimer(self, doShow):
        """Show or hide the filter timer
        (and thus hide or show the current filter name).
        """
        if doShow:
            self.filterTimerWdg.grid()
            self.filterCurrWdg.grid_remove()
        else:
            self.filterCurrWdg.grid()
            self.filterTimerWdg.grid_remove()
            
    def _updCameraConnState(self, cameraConnState, isCurrent, keyVar=None):
        stateStr = cameraConnState[0]
        descrStr = cameraConnState[1]
        if not stateStr:
            stateStr = "        "
        isConnected = stateStr.lower() == "connected"
        if isConnected:
            severity = RO.Constants.sevNormal
        else:
            severity = RO.Constants.sevWarning
        self.cameraConnStateWdg.set(stateStr, isCurrent=isCurrent, severity=severity)
    
    def _updTempLimits(self, ccdTempLimits, isCurrent, keyVar=None):
        #print "_updTempLimits(ccdTempLimits=%s, isCurrent=%s)" % (ccdTempLimits, isCurrent)
        for ind, (label, wdgSet) in enumerate(self.ccdTempLimitsWdgDict.iteritems()):
            tempLimit = ccdTempLimits[ind]
            if tempLimit == None:
                for wdg in wdgSet:
                    wdg.grid_remove()
            else:
                tempLimit = abs(tempLimit)
                if label.lower().endswith("low"):
                    tempLimit = -tempLimit
                for wdg in wdgSet:
                    wdg.grid()
                wdgSet[1].set(tempLimit)
    
    def _updCCDTemp(self, ccdTempInfo, isCurrent, keyVar=None):
        #print "_updCCDTemp(ccdTempInfo=%s, isCurrent=%s)" % (ccdTempInfo, isCurrent)
        ccdTemp, tempStatus = ccdTempInfo

        self.ccdTempWdg.set(ccdTemp, isCurrent)

        if tempStatus != None:
            tempStatus = tempStatus.lower()
        dispStr, tempSeverity = self.ccdTempStateDict.get(tempStatus, (tempStatus, RO.Constants.sevWarning))
        self.ccdTempStateWdg.set(dispStr, isCurrent = isCurrent, severity = tempSeverity)
    
    def _updCCDSetTemp(self, ccdSetTempInfo, isCurrent, keyVar=None):
        #print "_updCCDSetTemp(ccdSetTempInfo=%s, isCurrent=%s)" % (ccdSetTempInfo, isCurrent)
        ccdSetTemp, tempStatus = ccdSetTempInfo

        self.ccdSetTempWdg.set(ccdSetTemp, isCurrent)

        if tempStatus != None:
            tempStatus = tempStatus.lower()
        dispStr, tempSeverity = self.ccdTempStateDict.get(tempStatus, (tempStatus, RO.Constants.sevWarning))
        self.ccdSetTempStateWdg.set(dispStr, isCurrent = isCurrent, severity = tempSeverity)

    def _updFilter(self, filterName, isCurrent, keyVar=None):
        self._showFilterTimer(False)
        if filterName != None and filterName.lower() == "unknown":
            severity = RO.Constants.sevError
            self.filterUserWdg.setDefault(
                None,
                isCurrent = isCurrent,
            )
        else:
            severity = RO.Constants.sevNormal
            self.filterUserWdg.setDefault(
                filterName,
                isCurrent = isCurrent,
            )

        self.filterCurrWdg.set(
            filterName,
            isCurrent = isCurrent,
            severity = severity,
        )

    def _updFilterNames(self, filterNames, isCurrent, keyVar=None):
        if not filterNames or None in filterNames:
            return

        self.filterUserWdg.setItems(filterNames, isCurrent=isCurrent)
        
        # set width of slit and filter widgets
        # setting both helps keep the widget from changing size
        # if one is replaced by a timer.
        maxNameLen = max([len(fn) for fn in filterNames])
        maxNameLen = max(maxNameLen, 3) # room for "Out" for slitOPath
        self.filterCurrWdg["width"] = maxNameLen

    def _updFilterTime(self, filterTime, isCurrent, keyVar=None):
        if filterTime == None or not isCurrent:
            self._showFilterTimer(False)
            return
        
        self._showFilterTimer(True)
        self.filterTimerWdg.start(filterTime, newMax = filterTime)
    

if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
        
    testFrame = StatusConfigInputWdg (root)
    testFrame.pack()
    
    TestData.dispatch()
    
    testFrame.restoreDefault()

    def printCmds():
        try:
            cmdList = testFrame.getStringList()
        except ValueError, e:
            print "Command error:", e
            return
        if cmdList:
            print "Commands:"
            for cmd in cmdList:
                print cmd
        else:
            print "(no commands)"
    
    bf = Tkinter.Frame(root)
    cfgWdg = RO.Wdg.Checkbutton(bf, text="Config", defValue=True)
    cfgWdg.pack(side="left")
    Tkinter.Button(bf, text='Cmds', command=printCmds).pack(side='left')
    Tkinter.Button(bf, text='Current', command=testFrame.restoreDefault).pack(side='left')
    Tkinter.Button(bf, text='Demo', command=TestData.animate).pack(side='left')
    bf.pack()
    
    testFrame.gridder.addShowHideControl(testFrame.ConfigCat, cfgWdg)
    
    root.mainloop()
