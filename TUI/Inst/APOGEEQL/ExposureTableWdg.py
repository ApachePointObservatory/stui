#!/usr/bin/env python
"""Display data about APOGEE exposures for the current plate from the QuickLook actor

To do:
- Show plateID? (probably want to show it somewhere)

History:
2011-04-04 ROwen
2011-08-31 ROwen    Added support for predicted exposures.
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

        self.expDataList = DataObjects.DataList(("plateID", "expType"), "sortKey")

        qlModel = TUI.Models.getModel("apogeeql")
        qlModel.exposureData.addCallback(self._exposureDataCallback)
        
        self.headerWdg = RO.Wdg.Text(master=self, width=width, height=1, font="Courier", readOnly=True, helpURL=helpURL)
        self.headerWdg.grid(row=0, column=0, sticky="ew")
       
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

        self.headerWdg.insert("end", "Num     Name    Time Reads Dither  S/N")

        qlModel.exposureData.addCallback(self._exposureDataCallback)
        qlModel.predictedExposure.addCallback(self._predictedExposureCallback)
    
    def _predictedExposureCallback(self, keyVar):
        """New predictedExposure seen
        """
        if keyVar[0] == None:
            return
        self.expDataList.addItem(DataObjects.PredExpData(keyVar))
        self.redraw()
    
    def _exposureDataCallback(self, keyVar):
        """New exposureData seen
        """
        if keyVar[0] == None:
            return
        self.expDataList.addItem(DataObjects.ExpData(keyVar))
        self.redraw()

    
    def redraw(self):
        self.logWdg.clearOutput()
        netRealExpTime = 0
        netPredExpTime = 0
        netRealSNR = 0
        netPredSNRSq = 0
        dataList = self.expDataList.getList()
        sawReal = False
        sawPred = False
        for d in dataList:
            if not d.isPred:
                sawReal = True
                self.logWdg.addOutput("%3d %8s %7.1f %3d   %3s   %5.1f\n" % \
                    (d.expNum, d.expName, d.expTime, d.nReads, d.namedDitherPosition, d.snr),
                    severity=RO.Constants.sevNormal,
                )
                netRealExpTime = d.netExpTime
                netRealSNR = d.netSNR
            else:
                if not sawPred:
                    if sawReal:
                        self.logWdg.addOutput("Net Done     %7.1f             %5.1f\n\n" % \
                            (netRealExpTime, netRealSNR),
                            severity=RO.Constants.sevNormal,
                        )
                    else:
                        self.logWdg.addOutput("No finished exposures!\n\n",
                            severity=RO.Constants.sevWarning,
                        )
                sawPred = True
                self.logWdg.addOutput("%3d %8s %7.1f %3d   %3s   %5.1f\n" % \
                    (d.expNum, d.expName, d.expTime, d.nReads, d.namedDitherPosition, d.snrGoal),
                    severity=RO.Constants.sevWarning,
                )
                netPredExpTime += d.expTime
                netPredSNRSq += d.snrGoal**2

        if sawPred:
            # compute total = real + predicted SNR and exposure time
            totalSNR = math.sqrt(netRealSNR**2 + netPredSNRSq)
            totalExpTime = netRealExpTime + netPredExpTime 

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
