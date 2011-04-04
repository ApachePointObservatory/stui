#!/usr/bin/env python
"""Display data about APOGEE exposures for the current plate from the QuickLook actor

To do:
- Show plateID? (probably want to show it somewhere)

History:
2011-04-04 ROwen
"""
import Tkinter
import RO.Wdg
import TUI.Models
import DataObjects

class ExposureTableWdg(Tkinter.Frame):
    def __init__(self, master, width=40, helpURL=None):
        """Create an exposure table
        """
        Tkinter.Frame.__init__(self, master)

        self.expDataList = DataObjects.DataList("plateID", "expNum")

        qlModel = TUI.Models.getModel("apogeeql")
        qlModel.exposureData.addCallback(self._exposureDataCallback)
        
        self.headerWdg = RO.Wdg.Text(master=self, width=width, height=1, font="Courier", readOnly=True, helpURL=helpURL)
        self.headerWdg.grid(row=0, column=0, sticky="ew")
       
        self.logWdg = RO.Wdg.LogWdg(master=self, width=width, height=6, helpURL=helpURL)
        self.logWdg.grid(row=1, column=0, sticky="news")
        self.logWdg.text.configure(font="Courier")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.footerWdg = RO.Wdg.Text(master=self, width=width, height=1, font="Courier", readOnly=True, helpURL=helpURL)
        self.footerWdg.grid(row=2, column=0, sticky="ew")
    
        self.headerWdg.insert("end", "Num     Name   Time Reads Dither   S/N")
        self.footerFormatStr =       "Total       %7.1f              %5.1f"
        self.footerWdg.insert("end", self.footerFormatStr % (float("nan"), float("nan")))

        qlModel.exposureData.addCallback(self._exposureDataCallback)
    
    def _exposureDataCallback(self, keyVar):
        """New expData seen
        """
        if keyVar[0] == None:
            return
        self.expDataList.addItem(DataObjects.ExpData(keyVar))
        dataList = self.expDataList.getList()

        self.logWdg.clearOutput()
        strList = ["%3d %8s %6.1f %5d %6.1f %5.1f" % \
            (d.expNum, d.expName, d.expTime, d.nReads, d.ditherPos, d.snr) for d in dataList]
        self.logWdg.addOutput("\n".join(strList))

        self.footerWdg.delete("1.0", "end")
        if len(dataList) == 0:
            self.footerWdg.insert("end", self.footerFormatStr % (float("nan"), float("nan")))
            return
        lastItem = dataList[-1]
        self.footerWdg.insert("end", self.footerFormatStr % (lastItem.netExpTime, lastItem.netSNR))


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = ExposureTableWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

#     Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
