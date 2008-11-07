#!/usr/bin/env python
"""Configuration input panel for Agile.

To do:
- Make filter stuff work
- Make environment stuff work

History:
2008-10-24 ROwen    preliminary adaptation from DIS
2008-11-06 ROwen    Removed unused detector controls; the rest is not yet functional
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
    HelpPrefix = 'Instruments/%s/%sWin.html#' % (InstName, InstName)

    # category names
    ConfigCat = RO.Wdg.StatusConfigGridder.ConfigCat
    EnvironCat = 'environ'

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

        filtRow = gr.getNextRow()
        # reserve _DataWidth width
        blankLabel.grid(
            row = filtRow,
            column = 1,
            columnspan = 2,
        )
        gr.gridWdg (
            label = 'Filter',
            dataWdg = self.filterCurrWdg,
            units = None,
            cfgWdg = self.filterUserWdg,
            colSpan = 2,
        )
        self.filterTimerWdg.grid(
            row = filtRow,
            column = 1,
            columnspan = 2,
            sticky = "w",
        )
        self._showFilterTimer(False)

        self.model.filter.addIndexedCallback(self._updFilter)
        self.model.filterTime.addIndexedCallback(self._updFilterTime)

        # Temperature warning and individual temperatures
        
        self.environShowHideWdg = RO.Wdg.Checkbutton(
            master = self,
            text = "Environment",
            indicatoron = False,
            helpText = "Show/hide CCD temp",
            helpURL = self.HelpPrefix + "Environment",
        )
        
        self.environStatusWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "w",
            helpText = "Is temperature OK?",
            helpURL = self.HelpPrefix + "Environment",
        )

        gr.gridWdg (
            label = self.environShowHideWdg,
            dataWdg = self.environStatusWdg,
            colSpan = 2,
        )
        
        # hidable frame showing current pressure and temperatures

        self.envFrameWdg = Tkinter.Frame(master=self, borderwidth=1, relief="solid")
        
        # create header
        headStrSet = (
            "Sensor",
            "Curr",
            "Min",
            "Max",
        )
        
        for ind in range(len(headStrSet)):
            headLabel = RO.Wdg.Label(
                master = self.envFrameWdg,
                text = headStrSet[ind],
                anchor = "e",
                helpURL = self.HelpPrefix + "Environment",
            )
            headLabel.grid(row=0, column=ind, sticky="e")

        # temperatures

        self.tempHelpStrSet = (
            "temperature sensor",
            "current temperature",
            "minimum safe temperature",
            "maximum safe temperature",
        )
        
        # create blank widgets to display temperatures
        # this set is indexed by row (sensor)
        # and then by column (name, current temp, min temp, max temp)
        self.tempWdgSet = []
        nextCol = gr.getNextCol()
        
        gr.gridWdg (
            label = False,
            dataWdg = self.envFrameWdg,
            cfgWdg = False,
            colSpan = nextCol + 1,
            sticky = "w",
            numStatusCols = None,
            cat = self.EnvironCat,
        )
        
        self.columnconfigure(nextCol, weight=1)
            
        
        gr.allGridded()
        
        # add callbacks that deal with multiple widgets
        self.model.filterNames.addCallback(self._updFilterNames)
        self.environShowHideWdg.addCallback(self._doShowHide, callNow = False)
        self.model.ccdTemp.addCallback(self._updEnviron, callNow = False)
        self.model.ccdSetTemp.addCallback(self._updEnviron, callNow = False)
        self.model.ccdTempLimits.addCallback(self._updEnviron, callNow = False)
        self._updEnviron()
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
    
    def _addTempWdgRow(self):
        """Add a row of temperature widgets"""
        rowInd = len(self.tempWdgSet) + 2
        colInd = 0
        wdg = RO.Wdg.StrLabel(
            master = self.envFrameWdg,
            anchor = "e",
            helpText = self.tempHelpStrSet[colInd],
            helpURL = self.HelpPrefix + "Environment",
        )
        wdg.grid(row = rowInd, column = colInd, sticky="e")
        newWdgSet = [wdg]
        for colInd in range(1, 4):
            wdg = RO.Wdg.FloatLabel(
                master = self.envFrameWdg,
                precision = 1,
                anchor = "e",
                helpText = self.tempHelpStrSet[colInd],
                helpURL = self.HelpPrefix + "Environment",
            )
            wdg.grid(row = rowInd, column = colInd, sticky="ew")
            newWdgSet.append(wdg)
        colInd += 1
        wdg = RO.Wdg.StrLabel(
            master = self.envFrameWdg,
            text = "K",
            anchor = "w",
        )
        wdg.grid(row = rowInd, column = colInd, sticky="w")
        newWdgSet.append(wdg)
        self.tempWdgSet.append(newWdgSet)

    def _doShowHide(self, wdg=None):
        showTemps = self.environShowHideWdg.getBool()
        argDict = {self.EnvironCat: showTemps}
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
        
    def _updEnviron(self, *args, **kargs):
        isCurrent = True
        
        ccdTempAndCode, ccdTempCurr = self.model.ccdTemp.get()
        ccdSetTempAndCode, ccdTempCurr = self.model.ccdSetTemp.get()
        
        envState = "OK"
        
        envSeverity = RO.Constants.sevNormal
        
        if None not in ccdSetTempAndCode:
            ccdSetTemp, ccdSetTempCode = ccdSetTempAndCode
            ccdSetTempCode = ccdSetTempCode.lower()
            if ccdSetTempCode in ("low", "high"):
                envSeverity = RO.Constants.sevError
            elif ccdSetTempCode != "normal":
                envSeverity = RO.Constants.sevWarning
        else:
            ccdSetTemp = "nan"
            ccdSetTempCode = "?"
            envSeverity = RO.Constants.sevWarning
        
        if None not in ccdTempAndCode:
            ccdTemp, ccdTempCode = ccdTempAndCode
            ccdTempCode = ccdTempCode.lower()
            if ccdTempCode.startswith("very"):
                envSeverity = max(env.Severity, RO.Constants.sevError)
            elif ccdTempCode != "normal":
                envSeverity = max(envSeverity, RO.Constants.sevWarning)
        else:
            ccdTemp = "nan"
            ccdTempCode = "?"
            envSeverity = max(envSeverity, RO.Constants.sevWarning)

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
        self.slitOPathCurrWdg["width"] = maxNameLen

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
