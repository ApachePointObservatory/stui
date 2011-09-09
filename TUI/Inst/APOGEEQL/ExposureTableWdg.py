#!/usr/bin/env python
"""Display data about APOGEE exposures for the current plate from the QuickLook actor

To do:
- Show plateID? (probably want to show it somewhere)

History:
2011-04-04 ROwen
2011-08-31 ROwen    Added support for predicted exposures.
2011-09-02 ROwen    Updated for changes to DataList.
2011-09-09 ROwen    Bug fix: was not displaying net S/N if no predicted exposure data.
                    Added title that includes the plate ID.
                    Added exposure type to title.
"""
import math
import Tkinter
import RO.Constants
import RO.Wdg
import TUI.Models
import DataObjects

def fmt2(f1, f2):
    """Format two floats as f1/f2
    """
    return "%.1f/%.1f" % (f1, f2)

class ExposureTableWdg(Tkinter.Frame):
    def __init__(self, master, width=40, helpURL=None):
        """Create an exposure table
        """
        Tkinter.Frame.__init__(self, master)

        self.expDataList = DataObjects.DataList(
            sharedName = "plateIDExpType",
            uniqueName = "expNum",
        )
        self.predExpDataList = DataObjects.DataList(
            sharedName = "plateIDExpType",
            uniqueName = "expNum",
        )

        qlModel = TUI.Models.getModel("apogeeql")
        qlModel.exposureData.addCallback(self._exposureDataCallback)
        
        self.headerWdg = RO.Wdg.Text(
            master = self,
            width = width,
            height = 3,
            readOnly = True,
            helpText = "Data about finished and predicted exposures",
            helpURL = helpURL,
        )
        self.headerWdg.grid(row=0, column=0, sticky="ew")
        self.headerWdg.tag_configure("title", justify="center")
        self.headerWdg.tag_configure("header", font="courier")
       
        self.logWdg = RO.Wdg.LogWdg(
            master = self,
            width = width,
            height = 9,
            helpText = "Data about finished and predicted exposures",
            helpURL = helpURL,
        )
        self.logWdg.grid(row=1, column=0, sticky="news")
        self.logWdg.text.configure(font="Courier")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        qlModel.exposureData.addCallback(self._exposureDataCallback)
        qlModel.predictedExposure.addCallback(self._predictedExposureCallback)
        self.redraw()
    
    def _predictedExposureCallback(self, keyVar):
        """New predictedExposure seen
        """
        if keyVar[0] == None:
            return
        self.predExpDataList.addItem(DataObjects.PredExpData(keyVar))
        self.expDataList.sharedValue = self.predExpDataList.sharedValue
        self.redraw()
    
    def _exposureDataCallback(self, keyVar):
        """New exposureData seen
        """
        if keyVar[0] == None:
            return
        self.expDataList.addItem(DataObjects.ExpData(keyVar))
        self.predExpDataList.sharedValue = self.expDataList.sharedValue
        self.redraw()

    
    def redraw(self):
        self.headerWdg.delete("1.0", "end")
        self.logWdg.clearOutput()

        if self.expDataList or self.predExpDataList:
            plateID, expType = self.expDataList.sharedValue
            self.headerWdg.insert("end", "%s Exposures for Plate %s\n" % (expType, plateID), "title")
            self.headerWdg.insert("end", "\nNum   Name     Time  Reads Dither S/N", "header")
        else:
            self.headerWdg.insert("end", "No Exposure Data", "title")
            return
        
        netRealExpTime = 0
        netRealSNR = 0
        if self.expDataList:
            for d in self.expDataList:
                self.logWdg.addOutput("%2d  %8s %7.1f %3d   %3s   %5.1f\n" % \
                    (d.expNum, d.expName, d.expTime, d.nReads, d.namedDitherPosition, d.snr),
                )
                netRealExpTime = d.netExpTime
                netRealSNR = d.netSNR

        self.logWdg.addOutput("Net Done     %7.1f             %5.1f\n\n" % \
            (netRealExpTime, netRealSNR),
            severity=RO.Constants.sevNormal,
        )
        
        if self.predExpDataList:
            netPredExpTime = 0
            netPredSNRSq = 0

            for d in self.predExpDataList:
                self.logWdg.addOutput("%2d  %8s %7.1f %3d   %3s   %5.1f\n" % \
                    (d.expNum, d.expName, d.expTime, d.nReads, d.namedDitherPosition, d.snrGoal),
                    severity=RO.Constants.sevWarning,
                )
                netPredExpTime += d.expTime
                netPredSNRSq += d.snrGoal**2
            
            totalExpTime = netRealExpTime + netPredExpTime
            totalSNR = math.sqrt(netRealSNR**2 + netPredSNRSq)

            self.logWdg.addOutput("Done+Pred    %7.1f             %5.1f" % \
                (totalExpTime, totalSNR),
                severity=RO.Constants.sevWarning,
            )
        


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = ExposureTableWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
