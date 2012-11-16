#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-25 ROwen
2011-04-28 ROwen    Added support for collIndexer and ditherIndexer.
                    Added createTelemetryWdgSet to simplify the code.
2011-05-03 ROwen    Added array power.
                    Added Warning to the existing two summary values OK and Bad.
2011-05-06 ROwen    Improve formatting of values.
2011-05-09 ROwen    Improved formatting of vacuum.
2011-05-16 ROwen    Bug fix: was not listening to vacuumLimits or ln2Limits keywords.
2011-05-17 ROwen    Added alternate vacuum.
                    Modified to report thresholds instead of limits.
2012-11-14 ROwen    Stop using Checkbutton indicatoron=False; it is no longer supported on MacOS X.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models

_DataWidth = 7 # width of data columns

class FmtNum(object):
    """Format a floating-point number; return ? if unknown"""
    def __init__(self, fmtStr="%0.1f"):
        self.fmtStr=fmtStr

    def __call__(self, num):
        if num == None:
            return "?"
        return self.fmtStr % (num,)


class TelemetryWdgSet(object):
    _TelemetryCat = "telemetry"
    def __init__(self, gridder, colSpan=3, helpURL=None):
        """Create an TelemetryWdgSet
        
        Inputs:
        - gridder: an instance of RO.Wdg.Gridder;
            the widgets are gridded starting at the next row and default column
        - colSpan: the number of columns to span
        - helpURL: path to an HTML help file or None
        
        Note: you may wish to call master.columnconfigure(n, weight=1)
        where n is the last column of this widget set
        so that the telemetry widget panel can fill available space
        without resizing the columns of other widgets.
        """
        self.helpURL = helpURL
        
        self.gridder = gridder
        master = self.gridder._master
        
        self.model = TUI.Models.getModel("apogee")
        self.tuiModel = TUI.Models.getModel("tui")

        self.showHideWdg = RO.Wdg.Checkbutton(
            master = master,
            text = "Telemetry",
            helpText = "Show vacuum, temps, etc.?",
            helpURL = helpURL,
        )
        
        self.summaryWdg = RO.Wdg.StrLabel(
            master = master,
            anchor = "w",
            helpText = "Are vacuum, temps, etc. OK?",
            helpURL = helpURL,
        )
        gridder.gridWdg(self.showHideWdg, self.summaryWdg, sticky="w", colSpan=colSpan-1)
        
        # hidable frame showing current vacuum, LN2 and temperatures

        self.detailWdg = Tkinter.Frame(
            master = master,
            borderwidth = 1,
            relief = "solid",
        )
        self.gridder.gridWdg(False, self.detailWdg, colSpan=colSpan, sticky="w", cat=self._TelemetryCat)
        
        # create header
        headStrSet = (
            "Sensor",
            "Curr",
            "Thresh",
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

        row = 1

        self.vacuumWdgSet = self.createTelemetryWdgSet(
            row = row,
            name = "Vacuum",
            fmtFunc = FmtNum("%#0.2g"),
            units = "Torr",
            helpStrList = (
                "vacuum measured by main gauge",
                "current vacuum measured by main gauge",
                "vacuum alarm threshold",
            ),
        )
        row += 1

        self.altVacuumWdgSet = self.createTelemetryWdgSet(
            row = row,
            name = "Alt Vacuum",
            fmtFunc = FmtNum("%#0.2g"),
            units = "Torr",
            helpStrList = (
                "vacuum measured by alternate gauge",
                "current vacuum measured by alternate gauge",
                None,
            ),
        )
        row += 1

        # LN2 widgets
        
        self.ln2WdgSet = self.createTelemetryWdgSet(
            row = row,
            name = "LN2",
            fmtFunc = FmtNum("%0.0f"),
            units = "%",
            helpStrList = (
                "LN2 level",
                "current LN2 level",
                "LN2 alarm threshold",
            ),
        )
        row += 1

        self.arrayPowerWdgSet = self.createTelemetryWdgSet(
            row = row,
            name = "Array Power",
            fmtFunc = str,
            units = None,
            helpStrList = (
                "Array power",
                "Array power on, off or unknown",
                None,
            ),
        )
        row += 1
        
        # Temperature widgets

        self.tempStartRow = row
        # a set of temperature widgets; each entry is for a different sensor and includes these widgets:
        # (name, current temperature, minimum temperature, maximum temperature)
        self.tempWdgSet = []

        self.model.arrayPower.addCallback(self._updTelemetry, callNow = False)
        self.model.vacuum.addCallback(self._updTelemetry, callNow = False)
        self.model.vacuumAlarm.addCallback(self._updTelemetry, callNow = False)
        self.model.vacuumThreshold.addCallback(self._updTelemetry, callNow = False)
        self.model.ln2Level.addCallback(self._updTelemetry, callNow = False)
        self.model.ln2Alarm.addCallback(self._updTelemetry, callNow = False)
        self.model.ln2Threshold.addCallback(self._updTelemetry, callNow = False)
        self.model.tempNames.addCallback(self._updTelemetry, callNow = False)
        self.model.temps.addCallback(self._updTelemetry, callNow = False)
        self.model.tempAlarms.addCallback(self._updTelemetry, callNow = False)
        self.model.tempThresholds.addCallback(self._updTelemetry, callNow = False)
        
        self.showHideWdg.addCallback(self._doShowHide, callNow = True)
    
    def createTelemetryWdgSet(self, row, name, fmtFunc, units, helpStrList):
        """Create a set of telemetry widgets for one item of telemetry
        
        Inputs:
        - row: row number at which to grid the widgets
        - name: name of item being reported
        - fmtFunc: a formatting function that takes a value and returns a string
        - units: the units of the value; None if not relevant
        - helpStrList: a collection of three help strings for these:
            - name label
            - current value
            - threshold
           Specify None if you don't want a help string for a particular widget.
        """
        wdgSet = []
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = name,
            anchor = "e",
            helpText = helpStrList[0],
            helpURL = self.helpURL,
        )
        wdg.grid(row = row, column = len(wdgSet), sticky="e")
        wdgSet.append(wdg)
        for wdgInd in range(1, 3):
            wdg = RO.Wdg.Label(
                master = self.detailWdg,
                formatFunc = fmtFunc,
                width = _DataWidth,
                anchor = "e",
                helpText = helpStrList[wdgInd],
                helpURL = self.helpURL,
            )
            wdg.grid(row = row, column = len(wdgSet), sticky="ew")
            wdgSet.append(wdg)
        wdg = RO.Wdg.StrLabel(
            master = self.detailWdg,
            text = units,
            anchor = "w",
        )
        wdg.grid(row = row, column = len(wdgSet))
        return wdgSet

    def _addTempWdgRow(self):
        """Add a row of temperature widgets
        """
        newWdgSet = self.createTelemetryWdgSet(
            row = len(self.tempWdgSet) + self.tempStartRow,
            name = "",
            fmtFunc = FmtNum("%0.1f"),
            units = "K",
            helpStrList = (
                "temperature sensor",
                "current temperature",
                "temperature alarm threshold",
            ),
        )
        self.tempWdgSet.append(newWdgSet)

    def _doShowHide(self, wdg=None):
        argDict = {
            self._TelemetryCat: self.showHideWdg.getBool(),
        }
        self.gridder.showHideWdg (**argDict)

    def _updTelemetry(self, *args, **kargs):
        """Update telemetry data"""
        allCurrent = True
        allSeverity = RO.Constants.sevNormal
        
        # array power; note that ? is the normal state so only Off is bad

        allCurrent = allCurrent and self.model.arrayPower.isCurrent

        arrayStr = {False: "Off", True: "On"}.get(self.model.arrayPower[0], "?")
        if arrayStr == "Off":
            arraySev = RO.Constants.sevWarning
        else:
            arraySev = RO.Constants.sevNormal
            arrayPowerOK = True,
        self.arrayPowerWdgSet[0].setSeverity(arraySev)
        self.arrayPowerWdgSet[1].set(arrayStr,
            isCurrent = self.model.arrayPower.isCurrent, severity = arraySev)
        allSeverity = max(allSeverity, arraySev)
        
        # vacuum
        
        allCurrent = allCurrent and \
            self.model.vacuum.isCurrent and \
            self.model.vacuumAlarm.isCurrent and \
            self.model.vacuumThreshold.isCurrent

        if self.model.vacuumAlarm[0]:
            vacuumSev = RO.Constants.sevError
            vacuumOK = False
        else:
            vacuumSev = RO.Constants.sevNormal
            vacuumOK = True
        self.vacuumWdgSet[0].setSeverity(vacuumSev)
        self.vacuumWdgSet[1].set(self.model.vacuum[0],
            isCurrent = self.model.vacuum.isCurrent, severity = vacuumSev)
        self.vacuumWdgSet[2].set(self.model.vacuumThreshold[0],
            isCurrent = self.model.vacuumThreshold.isCurrent, severity = vacuumSev)
        allSeverity = max(allSeverity, vacuumSev)
        
        # alternate vacuum gauge (which has no associated alarm or limits)
        self.altVacuumWdgSet[1].set(self.model.vacuumAlt[0], isCurrent = self.model.vacuumAlt)

        # liquid nitrogen
        
        allCurrent = allCurrent and \
            self.model.ln2Level.isCurrent and \
            self.model.ln2Alarm.isCurrent and \
            self.model.ln2Threshold.isCurrent

        if self.model.ln2Alarm[0]:
            ln2Sev = RO.Constants.sevError
            ln2OK = False
        else:
            ln2Sev = RO.Constants.sevNormal
            ln2OK = True
        self.ln2WdgSet[0].setSeverity(ln2Sev)
        self.ln2WdgSet[1].set(self.model.ln2Level[0], isCurrent = self.model.ln2Level.isCurrent, severity = ln2Sev)
        self.ln2WdgSet[2].set(self.model.ln2Threshold[0],
                     isCurrent = self.model.ln2Threshold.isCurrent, severity = ln2Sev)
        allSeverity = max(allSeverity, ln2Sev)
        
        # temperatures

        tempNames = self.model.tempNames
        temps = self.model.temps
        tempAlarms = self.model.tempAlarms
        tempThresholds = self.model.tempThresholds

        if () in (tempNames, temps, tempAlarms):
            return
        allCurrent = allCurrent and tempNames.isCurrent and temps.isCurrent and \
            tempAlarms.isCurrent and tempThresholds.isCurrent

        if not (len(temps) == len(tempNames) == len(tempAlarms) == len(tempThresholds)):
            # temp data not self-consistent
            self.tuiModel.logMsg(
                "APOGEE temperature data not self-consistent; cannot display",
                severity = RO.Constants.sevWarning,
            )
            for wdgSet in self.tempWdgSet:
                for wdg in wdgSet:
                    wdg.setNotCurrent()
            return
            
        tempSet = zip(tempNames, temps, tempThresholds)
        isCurrSet = tempNames.isCurrent, temps.isCurrent, tempThresholds.isCurrent

        # add new widgets if necessary
        for ii in range(len(self.tempWdgSet), len(tempSet)):
            self._addTempWdgRow()
        
        # set widgets
        allTempsOK = True
        for ii in range(len(tempSet)):
            wdgSet = self.tempWdgSet[ii]
            infoSet = tempSet[ii]
            tCurr = infoSet[1]
            
            sevSet = [RO.Constants.sevNormal] * 3 # assume temp OK
            if tCurr != None:
                if tempAlarms[ii]:
                    allTempsOK = False
                    sevSet = [RO.Constants.sevError] * 4
                    allSeverity = max(allSeverity, RO.Constants.sevError)

            for wdg, info, isCurr, severity in zip(wdgSet, infoSet, isCurrSet, sevSet):
                wdg.set(info, isCurrent = isCurr, severity = severity)

        summaryStr = {
            RO.Constants.sevNormal: "OK",
            RO.Constants.sevWarning: "Warning",
            RO.Constants.sevError: "Bad",
        }.get(allSeverity, "?")
        self.summaryWdg.set(summaryStr, isCurrent = allCurrent, severity = allSeverity)
    
        # delete extra widgets, if any
        for ii in range(len(tempSet), len(self.tempWdgSet)):
            wdgSet = self.tempWdgSet.pop(ii)
            for wdg in wdgSet:
                wdg.grid_forget()
                del(wdg)


if __name__ == '__main__':
    import TUI.Base.Wdg
    root = RO.Wdg.PythonTk()
    
    import TestData
    tuiModel = TestData.tuiModel
    
    testFrame = Tkinter.Frame(root)
    gridder = RO.Wdg.Gridder(testFrame)
    envWdgSet = TelemetryWdgSet(gridder)
    testFrame.pack(side="top", expand=True)
    testFrame.columnconfigure(2, weight=1)

    statusBar = TUI.Base.Wdg.StatusBar(root)
    statusBar.pack(side="top", expand=True, fill="x")

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
