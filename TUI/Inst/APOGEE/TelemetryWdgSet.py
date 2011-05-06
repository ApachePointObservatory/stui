#!/usr/bin/env python
"""Display APOGEE instrument status

History:
2011-04-25 ROwen
2011-04-28 ROwen    Added support for collIndexer and ditherIndexer.
                    Added createTelemetryWdgSet to simplify the code.
2011-05-03 ROwen    Added array power.
                    Added Warning to the existing two summary values OK and Bad.
2011-05-06 ROwen    Improve formatting of values.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models

_DataWidth = 6 # width of data columns

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
            indicatoron = False,
            helpText = "Show/hide vacuum, temps, etc.",
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

        row = 1

        self.vacuumWdgSet = self.createTelemetryWdgSet(
            row = row,
            name = "Vacuum",
            fmtFunc = FmtNum("%0.1f"),
            units = "Torr",
            helpStrList = (
                "vacuum",
                "current vacuum",
                None,
                "maximum safe vacuum",
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
                "minimum normal LN2 level",
                "maximum normal LN2 level",
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
                None,
            ),
        )
        row += 1
        
        # Temperature widgets

        # create blank widgets to display temperatures
        # this set is indexed by row (sensor)
        # and then by column (name, current temp, min temp, max temp)
        self.tempStartRow = row
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
        self.model.tempMin.addCallback(self._updTelemetry, callNow = False)
        self.model.tempMax.addCallback(self._updTelemetry, callNow = False)
        
        self.showHideWdg.addCallback(self._doShowHide, callNow = True)
    
    def createTelemetryWdgSet(self, row, name, fmtFunc, units, helpStrList):
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
        for wdgInd in range(1, 4):
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
                "minimum safe temperature",
                "maximum safe temperature",
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
            self.model.vacuumLimits.isCurrent

        if self.model.vacuumAlarm[0]:
            vacuumSev = RO.Constants.sevError
            vacuumOK = False
        else:
            vacuumSev = RO.Constants.sevNormal
            vacuumOK = True
        self.vacuumWdgSet[0].setSeverity(vacuumSev)
        self.vacuumWdgSet[1].set(self.model.vacuum[0],
            isCurrent = self.model.vacuum.isCurrent, severity = vacuumSev)
        self.vacuumWdgSet[2].set(self.model.vacuumLimits[0],
            isCurrent = self.model.vacuumLimits.isCurrent, severity = vacuumSev)
        self.vacuumWdgSet[3].set(self.model.vacuumLimits[1],
            isCurrent = self.model.vacuumLimits.isCurrent, severity = vacuumSev)
        allSeverity = max(allSeverity, vacuumSev)

        # liquid nitrogen
        
        allCurrent = allCurrent and \
            self.model.ln2Level.isCurrent and \
            self.model.ln2Alarm.isCurrent and \
            self.model.ln2Limits.isCurrent

        if self.model.ln2Alarm[0]:
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
        allSeverity = max(allSeverity, ln2Sev)
        
        # temperatures

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
