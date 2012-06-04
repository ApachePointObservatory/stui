#!/usr/bin/env python
"""Monitor BOSS temperatures and LN2 levels

History:
2012-04-23 Elena Malanushenko, converted from a script to a window by Russell Owen
2012-06-04 ROwen    Fix clear button.
"""
import Tkinter
import matplotlib
import RO.Wdg
import TUI.Base.StripChartWdg
import TUI.Models

WindowName = "Inst.BOSS Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+33",
        visible = False,
        resizable = True,
        wdgFunc = BOSSTemperatureMonitorWdg,
    )

class BOSSTemperatureMonitorWdg(Tkinter.Frame):
    def __init__(self, master, timeRange=1800, width=8, height=4):
        """Create a BOSSTemperatureMonitorWdg
        
        Inputs:
        - master: parent Tk widget
        - timeRange: range of time displayed (seconds)
        - width: width of plot (inches)
        - height: height of plot (inches)
        """
        Tkinter.Frame.__init__(self, master)
        self.bossModel = TUI.Models.getModel("boss")

        self.stripChartWdg = TUI.Base.StripChartWdg.StripChartWdg(
            master = self,
            timeRange = timeRange,
            numSubplots = 2, 
            width = width,
            height = height,
            cnvTimeFunc = TUI.Base.StripChartWdg.TimeConverter(useUTC=True),
        )
        self.stripChartWdg.grid(row=0, column=0, sticky="nwes")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # the default ticks are not nice, so be explicit
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=range(0, 61, 5)))

        self.cameraNameList = (
            "sp1r0",
            "sp1b2",
            "sp2r0",
            "sp2b2",
        )
        self.cameraNameColorDict = {
            "sp1r0": "red",
            "sp1b2": "green",
            "sp2r0": "blue",
            "sp2b2": "black",
        }
        
        self.nomTempColorDict = dict() # dict of camera name: color
        self.nomTempLineDict = dict() # dict of camera name: nominal temperature line (if present)
        self.readTempLineDict = dict() # dict of camera name: read temperature line
        for cameraName in self.cameraNameList:
            self.addTemperatureLines(cameraName)
        
        
        self.stripChartWdg.showY(-140.0, -90.0, subplotInd=0)
        self.stripChartWdg.subplotArr[0].legend(loc=3, frameon=False)
        self.stripChartWdg.subplotArr[0].yaxis.set_label_text("CCDTemp (C)")

        self.stripChartWdg.plotKeyVar(
            label = "sp1",
            subplotInd = 1,
            keyVar = self.bossModel.SP1SecondaryDewarPress,
            keyInd = 0,
            color = "blue",
        )
        self.stripChartWdg.plotKeyVar(
            label = "sp2",
            subplotInd = 1,
            keyVar = self.bossModel.SP2SecondaryDewarPress,
            keyInd = 0,
            color = "red",
        )
        self.stripChartWdg.addConstantLine(10.0, subplotInd=1, color="grey")
        self.stripChartWdg.showY(0.1, 10.5, subplotInd=1)
        self.stripChartWdg.subplotArr[1].legend(loc=3, frameon=False)
        self.stripChartWdg.subplotArr[1].yaxis.set_label_text("Ln2 Pressure")

        self.clearWdg = RO.Wdg.Button(master = self, text = "C", callFunc = self.clearCharts)
        self.clearWdg.grid(row=0, column=0, sticky = "sw")
     
    def addTemperatureLines(self, cameraName):
        """Add read temperature line for a given camera; does not check if it already exists
        
        Also sets a callback for nominal temperature to draw a constant line
        """
        uprCameraName = cameraName.upper()

        tempNomKeyVar  = getattr(self.bossModel, "%sCCDTempNom"  % (uprCameraName,))
        def callFunc(keyVar, self=self, cameraName=cameraName):
            self.nomTempCallback(keyVar, cameraName=cameraName)
        tempNomKeyVar.addCallback(callFunc)

        tempReadKeyVar = getattr(self.bossModel, "%sCCDTempRead" % (uprCameraName,))

        color = self.cameraNameColorDict[cameraName]
        line = self.stripChartWdg.plotKeyVar(
            label = cameraName,
            subplotInd = 0,
            keyVar = tempReadKeyVar,
            keyInd = 0,
            color = color,
        )
        self.readTempLineDict[cameraName] = line
        return line
    
    def clearCharts(self, wdg=None):
        """Clear all strip charts
        """
        self.stripChartWdg.clear()
    
    def nomTempCallback(self, keyVar, cameraName):
        """Draw a constant line for a new value of a nominal temperature
        """
        color = self.cameraNameColorDict[cameraName]
        line = self.nomTempLineDict.pop(cameraName, None)
        if line:
            self.stripChartWdg.removeLine(line)
        
        nomTemp = keyVar[0]
        if nomTemp == None:
            return
        
        line = self.stripChartWdg.addConstantLine(
            nomTemp,
            color = color,
            linestyle = "--",
        )
        self.nomTempLineDict[cameraName] = line
        
        readLine = self.readTempLineDict[cameraName]
        readLine.line2d.set_label("%s (%0.1f)" % (cameraName, nomTemp))
        self.stripChartWdg.subplotArr[0].legend(loc=3, frameon=False)
 

if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
#    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
       
        
