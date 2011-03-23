#!/usr/bin/env python
"""Display APOGEE QuickLook actor

To do:
- Add current exposure status table

- Exposure table:
  - Show plateID

- S/N graph:
  - make sure last data point is shown (right now it's truncated for some reason--because upper limit = 5?)
  - display vertical line if/when the data is available
  - display fit line
  - consider modifying S/N scale to sqrt so fit is a line (that's a lot of work I suspect)
  - display only integers on horizontal ticks

History:
2011-03-22 ROwen
"""
import Tkinter
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RO.Wdg
import TUI.PlaySound
import TUI.Models


class DataList(object):
    """Hold a sorted collection of unique data items
    """
    def __init__(self, sharedName, keyName):
        """Create a data list sorted by a specified key, with unique values for each key
        
        @param[in] sharedName: item attribute whose value is shared by all items;
            when an item is added with a new value for this attribute the list is reset
        @param[in] keyName: item attribute by which the items are sorted
        """
        self._sharedName = str(sharedName)
        self._keyName = str(keyName)
        self._sharedValue = None
        self._keyItemDict = dict()
    
    def addItem(self, item):
        """Add an item. If an item already exists with the same key then replace it.
        """
        sharedValue = getattr(item, self._sharedName)
        key = getattr(item, self._keyName)
        if sharedValue != self._sharedValue:
            self._keyItemDict = dict()
            self._sharedValue = sharedValue
        self._keyItemDict[key] = item
    
    def clear(self):
        """Clear all data
        """
        self._keyItemDict = dict()
    
    def getList(self):
        """Return the data as a sorted list
        """
        return [self._keyItemDict[k] for k in sorted(self._keyItemDict.keys())]
    
    def getSharedValue(self):
        """Get the shared value
        """
        return self._sharedName
        

class ExpData(object):
    """Data about an exposure
    """
    def __init__(self, keyVar):
        """Construct an ExpData from a apogeeql exposureList keyVar
        """
        self.plateID = keyVar[0]
        self.expNum = keyVar[1]
        self.expName = keyVar[2]
        self.expTime = keyVar[3]
        self.nReads = keyVar[4]
        self.ditherPos = keyVar[5]
        self.snr = keyVar[6]
        self.netExpTime = keyVar[7]
        self.netSNR = keyVar[8]


class UTRData(object):
    """Data about an up-the-ramp read
    """
    def __init__(self, keyVar):
        """Construct an ExpData from a apogeeql exposureList keyVar
        """
        self.expName = keyVar[0]
        self.readNum = keyVar[1]
        self.snr = keyVar[2]


class QuickLookWdg(Tkinter.Frame):
    """A widget that displays the results of APOGEE QuickLook
    """
    def __init__(self, master, helpURL=None):
        Tkinter.Frame.__init__(self, master)
        self.qlModel = TUI.Models.getModel("apogeeql")
        self.expDataList = DataList("plateID", "expNum")
        self.utrReadDataList = DataList("expName", "readNum")
        self.expNumDataDict = dict()
        self.plateID = None
        
        self.expLogWdg = ExposureLogWdg(master=self)
        self.expLogWdg.grid(row=0, column=0, sticky="ew")
        
        self.snrGraphWdg = SNRGraphWdg(master=self, width=4, height=4)
        self.snrGraphWdg.grid(row=1, column=0, sticky="news")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.qlModel.exposureList.addCallback(self._exposureListCallback)
        self.qlModel.snrData.addCallback(self._snrDataCallback)
    
    def _exposureListCallback(self, keyVar):
        if keyVar[0] == None:
            return
        self.expDataList.addItem(ExpData(keyVar))
        dataList = self.expDataList.getList()
        self.expLogWdg.updateExpData(dataList)
    
    def _snrDataCallback(self, keyVar):
        if keyVar[0] == None:
            return
        self.utrReadDataList.addItem(UTRData(keyVar))
        dataList = self.utrReadDataList.getList()
        self.snrGraphWdg.updateUTRReadData(dataList)
        

class ExposureLogWdg(Tkinter.Frame):
    def __init__(self, master, width=40, helpURL=None):
        """Create an exposure table
        """
        Tkinter.Frame.__init__(self, master)

        self.qlModel = TUI.Models.getModel("apogeeql")
        
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

    def updateExpData(self, expDataList):
        """Exposure data has been updated
        
        @param[in] expDataList: a list of ExpData objects
        """
        self.logWdg.clearOutput()
        strList = ["%3d %8s %6.1f %5d %6.1f %5.1f" % \
            (d.expNum, d.expName, d.expTime, d.nReads, d.ditherPos, d.snr) for d in expDataList]
        self.logWdg.addOutput("\n".join(strList))

        self.footerWdg.delete("1.0", "end")
        if len(expDataList) == 0:
            self.footerWdg.insert("end", self.footerFormatStr % (float("nan"), float("nan")))
            return
        lastItem = expDataList[-1]
        self.footerWdg.insert("end", self.footerFormatStr % (lastItem.netExpTime, lastItem.netSNR))


class SNRGraphWdg(Tkinter.Frame):
    def __init__(self, master, width, height):
        """Create a SN graph of S/N at H=12.0 vs. up-the-ramp read number

        Internal note: useful keyword arguments for matplotlib lines
        - color: color of line
        - linestyle: style of line (defaults to a solid line); "" for no line, "- -" for dashed, etc.
        - marker: marker shape, e.g. "+"
        """
        Tkinter.Frame.__init__(self, master)

        self.qlModel = TUI.Models.getModel("apogeeql")
        
        self.figure = matplotlib.figure.Figure(figsize=(width, height), frameon=True)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="news")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.snrAxis = self.figure.add_subplot(1, 1, 1)
        self.dataLine = matplotlib.lines.Line2D([], [], linestyle="", marker="+")
        self.snrAxis.add_line(self.dataLine)
        self.snrTargetLine = None
        self.snrAxis.set_title("S/N at H=12.0 vs. UTR Read")
        
        # monitor axes limits and related keywords
        self.qlModel.snrAxisRange.addCallback(self._snrAxisRangeCallback)
        self.qlModel.snrH12Target.addCallback(self._snrH12TargetCallback)
        self.qlModel.snrLinFit.addCallback(self._snrLinFitCallback)
        
    def updateUTRReadData(self, utrReadDataList):
        """UTR Read data has been updated
        
        @param[in] utrReadDataList: a list of ExpData objects
        """
        numList = [elt.readNum for elt in utrReadDataList]
        snrList = [elt.snr for elt in utrReadDataList]
        self.dataLine.set_data(numList, snrList)
        xMin = numList[0]
        xMax = max(numList[-1], xMin + 1)
        self.snrAxis.set_xlim(xMin, xMax)
        self.canvas.draw()
    
    def _snrAxisRangeCallback(self, keyVar):
        """snrAxisRange has been updated
        """
        if None in keyVar:
            return
        print "set Y limits"
        self.snrAxis.set_ylim(keyVar[0], keyVar[1], auto=False)
        self.canvas.draw()
        
    def _snrH12TargetCallback(self, keyVar):
        """snrH12Target has been updated
        """
        if self.snrTargetLine:
            self.snrAxis.lines.remove(self.snrTargetLine)
        if None in keyVar:
            return
        self.snrTargetLine = self.snrAxis.axhline(keyVar[0], color="green")
        
    def _snrLinFitCallback(self, keyVar):
        """snrLinFit has been updated
        """
        print "Warning: _snrLinFitCallback not yet implemented"
        pass
        
        


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = QuickLookWdg(tuiModel.tkRoot)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
