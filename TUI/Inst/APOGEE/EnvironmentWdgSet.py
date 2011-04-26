#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-25 ROwen
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models

_DataWidth = 6 # width of environment value columns

class EnvironmentWdgSet(object):
    _EnvironCat = "environ"
    def __init__(self, gridder, colSpan=3, helpURL=None):
        """Create an EnvironmentWdgSet
        
        Inputs:
        - gridder: an instance of RO.Wdg.Gridder;
            the widgets are gridded starting at the next row and default column
        - colSpan: the number of columns to span
        - helpURL: path to an HTML help file or None
        
        Note: you may wish to call master.columnconfigure(n, weight=1)
        where n is the last column of this widget set
        so that the environment widget panel can fill available space
        without resizing the columns of other widgets.
        """
        self.helpURL = helpURL
        
        self.gridder = gridder
        master = self.gridder._master
        
        self.model = TUI.Models.getModel("apogee")
        self.tuiModel = TUI.Models.getModel("tui")

        self.showHideWdg = RO.Wdg.Checkbutton(
            master = master,
            text = "Environment",
            indicatoron = False,
            helpText = "Show/hide vacuum, LN2 and temps",
            helpURL = helpURL,
        )
        
        self.summaryWdg = RO.Wdg.StrLabel(
            master = master,
            anchor = "w",
            helpText = "Are vacuum, LN2 and temps OK?",
            helpURL = helpURL,
        )
        gridder.gridWdg(self.showHideWdg, self.summaryWdg, sticky="w", colSpan=colSpan-1)
        
        # hidable frame showing current vacuum, LN2 and temperatures

        self.detailWdg = Tkinter.Frame(
            master = master,
            borderwidth = 1,
            relief = "solid",
        )
        self.gridder.gridWdg (False, self.detailWdg, colSpan=colSpan, sticky="w", cat=self._EnvironCat)
        
        # create header
        headStrSet = (
            "Sensor",
            "Curr",
            "Min",
            "Max",
        )
        
        for ii in range(len(headStrSet)):
            headLabel = RO.Wdg.Label(
                master = self.detailWdg,
                text = headStrSet[ii],
                anchor = "e",
                helpURL = helpURL,
            )
            headLabel.grid(row=0, column=ii, sticky="e")

        # Vacuum widgets: name label, current, min, max

        vacuumHelpStrs = (
            "vacuum",
            "current vacuum",
            None,
            "maximum safe vacuum",
        )

        row = 1
        newWdgSet = []
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = "Vacuum",
            anchor = "e",
            helpText = vacuumHelpStrs[0],
            helpURL = helpURL,
        )
        wdg.grid(row = row, column = len(newWdgSet), sticky="e")
        newWdgSet.append(wdg)
        for wdgInd in range(1, 4):
            wdg = RO.Wdg.Label(
                master = self.detailWdg,
                formatFunc = fmtExp,
                width = _DataWidth,
                anchor = "e",
                helpText = vacuumHelpStrs[wdgInd],
                helpURL = helpURL,
            )
            wdg.grid(row = row, column = len(newWdgSet), sticky="ew")
            newWdgSet.append(wdg)
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = "Torr",
            anchor = "w",
        )
        wdg.grid(row = row, column = len(newWdgSet), sticky="w")
        self.vacuumWdgSet = newWdgSet

        # LN2 widgets
        
        ln2HelpStrs = (
            "LN2 level",
            "current LN2 level",
            "minimum normal LN2 level",
            "maximum normal LN2 level",
        )

        row += 1
        newWdgSet = []
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = "LN2",
            anchor = "e",
            helpText = ln2HelpStrs[0],
            helpURL = helpURL,
        )
        wdg.grid(row = row, column = len(newWdgSet), sticky="e")
        newWdgSet.append(wdg)
        for wdgInd in range(1, 4):
            wdg = RO.Wdg.Label(
                master = self.detailWdg,
                width = _DataWidth,
                anchor = "e",
                helpText = ln2HelpStrs[wdgInd],
                helpURL = helpURL,
            )
            wdg.grid(row = row, column = len(newWdgSet), sticky="ew")
            newWdgSet.append(wdg)
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = "%",
            anchor = "w",
        )
        wdg.grid(row = row, column = len(newWdgSet), sticky="w")
        self.ln2WdgSet = newWdgSet

        # Temperature widgets

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
        
        self.model.vacuum.addCallback(self._updEnviron, callNow = False)
        self.model.vacuumAlarm.addCallback(self._updEnviron, callNow = False)
        self.model.vacuumThreshold.addCallback(self._updEnviron, callNow = False)
        self.model.ln2Level.addCallback(self._updEnviron, callNow = False)
        self.model.ln2Alarm.addCallback(self._updEnviron, callNow = False)
        self.model.ln2Threshold.addCallback(self._updEnviron, callNow = False)
        self.model.tempNames.addCallback(self._updEnviron, callNow = False)
        self.model.temps.addCallback(self._updEnviron, callNow = False)
        self.model.tempAlarms.addCallback(self._updEnviron, callNow = False)
        self.model.tempMin.addCallback(self._updEnviron, callNow = False)
        self.model.tempMax.addCallback(self._updEnviron, callNow = False)
        
        self.showHideWdg.addCallback(self._doShowHide, callNow = True)

    def _addTempWdgRow(self):
        """Add a row of temperature widgets
        """
        row = len(self.tempWdgSet) + 3
        newWdgSet = []
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            anchor = "e",
            helpText = self.tempHelpStrSet[0],
            helpURL = self.helpURL,
        )
        wdg.grid(row = row, column = len(newWdgSet), sticky="e")
        newWdgSet.append(wdg)
        for wdgInd in range(1, 4):
            wdg = RO.Wdg.FloatLabel(
                master = self.detailWdg,
                precision = 1,
                anchor = "e",
                helpText = self.tempHelpStrSet[wdgInd],
                helpURL = self.helpURL,
            )
            wdg.grid(row = row, column = len(newWdgSet), sticky="ew")
            newWdgSet.append(wdg)
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = "K",
            anchor = "w",
        )
        wdg.grid(row = row, column = len(newWdgSet), sticky="w")
        self.tempWdgSet.append(newWdgSet)

    def _doShowHide(self, wdg=None):
        argDict = {
            self._EnvironCat: self.showHideWdg.getBool(),
        }
        self.gridder.showHideWdg (**argDict)

    def _updEnviron(self, *args, **kargs):
        """Update environmental data"""
        allCurrent = True
        
        # handle vacuum
        
        allCurrent = allCurrent and \
            self.model.vacuum.isCurrent and \
            self.model.vacuumAlarm.isCurrent and \
            self.model.vacuumLimits.isCurrent

        if  self.model.vacuumAlarm[0] == 1:
            vacuumSev = RO.Constants.sevError
            vacuumOK = False
        else:
            vacuumSev = RO.Constants.sevNormal
            vacuumOK = True
        self.vacuumWdgSet[0].setSeverity(vacuumSev)
        self.vacuumWdgSet[1].set(self.model.vacuum[0], isCurrent = self.model.vacuum.isCurrent, severity = vacuumSev)
        self.vacuumWdgSet[2].set(self.model.vacuumLimits[0],
                     isCurrent = self.model.vacuumLimits.isCurrent, severity = vacuumSev)
        self.vacuumWdgSet[3].set(self.model.vacuumLimits[1],
                     isCurrent = self.model.vacuumLimits.isCurrent, severity = vacuumSev)

        # liquid nitrogen
        
        allCurrent = allCurrent and \
            self.model.ln2Level.isCurrent and \
            self.model.ln2Alarm.isCurrent and \
            self.model.ln2Limits.isCurrent

        if  self.model.ln2Alarm[0] == 1:
            ln2Sev = RO.Constants.sevError
            ln2OK = False
        else:
            ln2Sev = RO.Constants.sevNormal
            ln2OK = True
        self.ln2WdgSet[0].setSeverity(ln2Sev)
        self.ln2WdgSet[1].set(self.model.ln2Level[0], isCurrent = self.model.ln2Level.isCurrent, severity = ln2Sev)
        self.ln2WdgSet[2].set(self.model.ln2Limits[0],
                     isCurrent = self.model.ln2Limits.isCurrent, severity = ln2Sev)
        self.ln2WdgSet[3].set(self.model.ln2Limits[1],
                     isCurrent = self.model.ln2Limits.isCurrent, severity = ln2Sev)
        
        # handle temperatures

        tempNames = self.model.tempNames
        temps = self.model.temps
        tempAlarms = self.model.tempAlarms
        tempMin = self.model.tempMin
        tempMax = self.model.tempMax

        if () in (tempNames, temps, tempAlarms):
            return
        allCurrent = allCurrent and tempNames.isCurrent and temps.isCurrent and \
            tempAlarms.isCurrent and tempMin.isCurrent and tempMax.isCurrent

        if not (len(temps) == len(tempNames) == len(tempAlarms) == len(tempMin) == len(tempMax)):
            # temp data not self-consistent
            self.tuiModel.logMsg(
                "APOGEE temperature data not self-consistent; cannot display",
                severity = RO.Constants.sevWarning,
            )
            for wdgSet in self.tempWdgSet:
                for wdg in wdgSet:
                    wdg.setNotCurrent()
            return
            
        tempSet = zip(tempNames, temps, tempMin, tempMax)
        isCurrSet = tempNames.isCurrent, temps.isCurrent, tempMin.isCurrent, tempMax.isCurrent

        # add new widgets if necessary
        for ii in range(len(self.tempWdgSet), len(tempSet)):
            self._addTempWdgRow()
        
        # set widgets
        allTempsOK = True
        for ii in range(len(tempSet)):
            wdgSet = self.tempWdgSet[ii]
            infoSet = tempSet[ii]
            tCurr = infoSet[1]
            
            sevSet = [RO.Constants.sevNormal] * 4 # assume temp OK
            if tCurr != None:
                if tempAlarms[ii]:
                    allTempsOK = False
                    sevSet = [RO.Constants.sevError] * 4

            for wdg, info, isCurr, severity in zip(wdgSet, infoSet, isCurrSet, sevSet):
                wdg.set(info, isCurrent = isCurr, severity = severity)

        if vacuumOK and ln2OK and allTempsOK:
            self.summaryWdg.set(
                "OK",
                isCurrent = allCurrent,
                severity = RO.Constants.sevNormal,
            )
        else:
            self.summaryWdg.set(
                "Bad", 
                isCurrent = allCurrent,
                severity = RO.Constants.sevError,
            )
    
        # delete extra widgets, if any
        for ii in range(len(tempSet), len(self.tempWdgSet)):
            wdgSet = self.tempWdgSet.pop(ii)
            for wdg in wdgSet:
                wdg.grid_forget()
                del(wdg)
    
        

def fmtExp(num):
    """Formats a floating-point number as x.xe-x"""
    retStr = "%.1e" % (num,)
    if retStr[-2] == '0':
        retStr = retStr[0:-2] + retStr[-1]
    return retStr


if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()
    
    import TestData
    tuiModel = TestData.tuiModel
    
    testFrame = Tkinter.Frame(root)
    gridder = RO.Wdg.Gridder(testFrame)
    envWdgSet = EnvironmentWdgSet(gridder)
    testFrame.pack(side="top", expand=True)
    testFrame.columnconfigure(2, weight=1)

    statusBar = TUI.Base.Wdg.StatusBar(root)
    statusBar.pack(side="top", expand=True, fill="x")

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
