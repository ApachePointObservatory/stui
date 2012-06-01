#!/usr/bin/env python
"""Monitor BOSS temperatures and LN2 levels

History:
2012-04-23 Elena Malanushenko, converted from a script to a window by Russell Owen
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
    def __init__(self, master, timeRange=700, width=8, height=4):
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
        self.stripChartWdg.grid(row=1, column=0, sticky="nwes")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # the default ticks are not nice, so be explicit
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=range(0, 61, 2)))

        buttonFrame = Tkinter.Frame(self)
        
        RO.Wdg.StrLabel(
            master = buttonFrame,
            text = "Show:",
        ).pack(side="left")
        self.cameraNameList = (
            "sp1r0",
            "sp1b2",
            "sp2r0",
            "sp2b2",
        )
        self.cameraColorDict = {
            "sp1r0": "red",
            "sp1b2": "green",
            "sp2r0": "blue",
            "sp2b2": "black",
        }
        
        self.tempLinesDict = {}
        for cameraName in self.cameraNameList:
            self.tempLinesDict[cameraName] = []
        
        self.cameraWdgList = []
        for cameraName in self.cameraNameList:
            cameraWdg = RO.Wdg.Checkbutton(
                master = buttonFrame,
                text = cameraName,
                defValue = True,
                helpText = "show/hide temperature for %s" % (cameraName,),
                callFunc = self.showHideCameraLines,
            )
            cameraWdg.pack(side="left")
            self.cameraWdgList.append(cameraWdg)

        buttonFrame.grid(row=0, column=0, sticky="w")
        
        self.showHideCameraLines()
                        
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
        self.stripChartWdg.subplotArr[1].yaxis.set_label_text("Ln2")
    
    def showHideCameraLines(self, dum=None):
        """Show or hide all camera lines
        """
        for wdg in self.cameraWdgList:
            cameraName = wdg["text"]
            lineList = self.tempLinesDict[cameraName]
            
            if wdg.getBool():
                if lineList:
                    continue # lines already exist

                lineList[:] = self.addLines(cameraName = cameraName)
            else:
                if not lineList:
                    continue # no lines to remove

                for line in lineList:
                    self.stripChartWdg.removeLine(line)
                lineList[:] = []
     
    def addLines(self, cameraName):
        """Add lines for a given camera; does not check if they already exist
        """
        lineList = []
        lineColor = self.cameraColorDict[cameraName]
        uprCameraName = cameraName.upper()
        tempNomKeyVar  = getattr(self.bossModel, "%sCCDTempNom"  % (uprCameraName,))
        tempReadKeyVar = getattr(self.bossModel, "%sCCDTempRead" % (uprCameraName,))

        constVal = tempNomKeyVar[0]
        if constVal != None:
            constLine = self.stripChartWdg.addConstantLine(constVal, subplotInd=0, color="grey")
            lineList.append(constLine)
            
        line = self.stripChartWdg.plotKeyVar(
            label = cameraName,
            subplotInd = 0,
            keyVar = tempReadKeyVar,
            keyInd = 0,
            color = lineColor,
        )
        lineList.append(line)
        return lineList
 

if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
#    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
       
        
