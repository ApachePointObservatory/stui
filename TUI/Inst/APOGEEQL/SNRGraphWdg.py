#!/usr/bin/env python
"""Display APOGEE QuickLook actor

To do:
- make sure to display only integers on horizontal ticks;
  presently it may display floats depending on the range
- try to figure out how to implement a help contextual menu

History:
2011-04-26 ROwen
"""
import Tkinter
import numpy
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RO.Wdg
import TUI.PlaySound
import TUI.Models
import DataObjects

class SNRGraphWdg(Tkinter.Frame):
    def __init__(self, master, width, height, helpURL=None):
        """Create a SN graph of S/N at H=12.0 vs. up-the-ramp read number
        
        Inputs:
        - master: master Tk widget
        - width: width of graph (inches)
        - height: height of graph (inches)
        - helpURL: URL of help file; warning: this is IGNORED because I don't yet know how to enable
            contextual menus in matplotlig graph widgets

        Internal note: useful keyword arguments for matplotlib lines
        - color: color of line
        - linestyle: style of line (defaults to a solid line); "" for no line, "- -" for dashed, etc.
        - marker: marker shape, e.g. "+"
        - markersize
        - markeredgewidth (basically thickness)
        """
        Tkinter.Frame.__init__(self, master)

        self.utrReadDataList = DataObjects.DataList("expNum", "readNum")
        qlModel = TUI.Models.getModel("apogeeql")
        
        self.figure = matplotlib.figure.Figure(figsize=(width, height), frameon=True)
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="news")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.axes = self.figure.add_subplot(1, 1, 1)
        self.dataLine = matplotlib.lines.Line2D([], [], linestyle="", marker="+")
        self.fitLine = matplotlib.lines.Line2D([], [], linestyle="dotted")
        self.axes.add_line(self.dataLine)
        self.axes.add_line(self.fitLine)
        self.snrGoalLine = None
        self.estReadsLine = None
        self.axes.set_title("S/N at H=12.0 vs. UTR Read")
        
        qlModel.exposureData.addCallback(self._exposureDataCallback)
        qlModel.snrAxisRange.addCallback(self._snrAxisRangeCallback)
        qlModel.utrData.addCallback(self._utrDataCallback)
    
    def _exposureDataCallback(self, keyVar):
        """exposureData keyVar callback. Used to display the target S/N.
        """
        if self.snrGoalLine:
            self.axes.lines.remove(self.snrGoalLine)
        snrGoal = keyVar[5]
        if snrGoal != None:
            self.snrGoalLine = self.axes.axhline(snrGoal, color="green")
    
    def _snrAxisRangeCallback(self, keyVar):
        """snrAxisRange has been updated
        """
        if None in keyVar:
            return
        self.axes.set_ylim(keyVar[0], keyVar[1], auto=False)
        self.canvas.draw()

    def _utrDataCallback(self, keyVar):
        """utrData keyVar callback
        """
        if keyVar[0] == None:
            return
        self.utrReadDataList.addItem(DataObjects.UTRData(keyVar))
        dataList = self.utrReadDataList.getList()
        
        numList = [elt.readNum for elt in dataList]
        snrList = [elt.snr for elt in dataList]
        estReads = None
        fitCoeffs = None
        self.dataLine.set_data(numList, snrList)
        if numList:
            estReads = dataList[-1].numReadsToTarget
            fitCoeffs = dataList[-1].snrRecentLinFitCoeffs
            xMin = numList[0]
            xMax = max(numList[-1], estReads)
        else:
            xMin = 1
            xMax = 1
        xMin = xMin - 0.49
        xMax = xMax + 0.49
        self.axes.set_xlim(xMin, xMax)

        if self.estReadsLine:
            self.axes.lines.remove(self.estReadsLine)
        if estReads != None:
            self.estReadsLine = self.axes.axvline(estReads, color="green")
            
        # code to draw fit line goes here.
        # dataList is empty then set line data to the empty list; otherwise:
        # evaluate fit over range xMin to xMax
        # set data and display it
        if fitCoeffs == None:
            fitReadNumArr = []
            fitSnrArr = []
        else:
            dx = (xMax - xMin) / 100.0
            fitReadNumArr = numpy.arange(xMin, xMax, dx)
            fitSnrArr = numpy.sqrt(fitReadNumArr * fitCoeffs[1] + fitCoeffs[0])
        print "fitCoeffs=", fitCoeffs
        print "fitReadNumArr=", fitReadNumArr
        print "fitSnrArr=", fitSnrArr
        self.fitLine.set_data(fitReadNumArr, fitSnrArr)

        self.canvas.draw()


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    import TestData
    tuiModel = TestData.tuiModel

    testFrame = SNRGraphWdg(tuiModel.tkRoot, width=4, height=4)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
