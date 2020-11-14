#!/usr/bin/env python
"""Display APOGEE QuickLook actor

TEST LINE ADD/REMOVE BEFORE FIXING TO VERIFY BUG
AND TO VERIFY MY FIX WORKS

ADD LINE OBJECT TO SIMPLIFY MANAGEMENT; DO NOT REDRAW LINE IF IT IS VISIBLE AND VALUE IS SAME

To do:
- make sure to display only integers on horizontal ticks;
  presently it may display floats depending on the range
- try to figure out how to implement a help contextual menu

History:
2011-04-26 ROwen
2011-05-26 ROwen    Commented out diagnostic print statements
2011-06-14 ROwen    Plot S/N^2 instead of S/N.
                    Show fit of all points instead of fit of recent points.
2011-07-19 ROwen    Make sure x range always includes nReads (if present and > 0).
                    Only display a line for numReadsToTarget if value > 0.
2011-09-02 ROwen    Updated for changes to DataList.
2011-09-21 ROwen    Fix ticket #1442: exception in _utrDataCallback: I was not clearing self.estReadsLine
                    after deleting the line from self.axes.lines. Fixed using the HVLine object.
                    My code to make sure the range included estNExp had no effect.
2012-06-04 ROwen    Removed unused import
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import Tkinter
import numpy
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import RO.Wdg
import TUI.Models
from . import DataObjects

class HVLine(object):
    """A horizontal or vertical line on a matplotlib Axes object
    
    You can show the line at a specified location or clear it
    """
    def __init__(self, axes, isHoriz, **lineKeyArgs):
        """Create an HVLine
        
        Inputs:
        - axes: an instance of matplotlib Axes
        - isHoriz: if True the line is horizontal, else vertical
        **lineKeyArgs: all remaining keyword arguments are used when creating the line
        """
        self.axes = axes
        if isHoriz:
            self.lineFunc = self.axes.axhline
        else:
            self.lineFunc = self.axes.axvline
        self.line = None
        self.lineKeyArgs = lineKeyArgs
    
    def show(self, value):
        """Show a line with the specified value; None clears the line
        """
        self.clear()
        if value is None:
            return

        self.line = self.lineFunc(value, **self.lineKeyArgs)
        self.currValue = value
    
    def clear(self):
        """Clear the line
        """
        if self.line:
            try:
                self.axes.lines.remove(self.line)
            finally:
                self.line = None
        

class SNRGraphWdg(Tkinter.Frame):
    def __init__(self, master, width, height, helpURL=None):
        """Create a SN graph of S/N^2 at H=12.0 vs. up-the-ramp read number
        
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

        self.utrReadDataList = DataObjects.DataList(
            sharedName = "expNum",
            uniqueName = "readNum",
        )
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
        self.snrGoalLine = HVLine(self.axes, isHoriz=True, color="green")
        self.estReadsLine = HVLine(self.axes, isHoriz=False, color="green")
        self.axes.set_title("S/N^2 at H=12.0 vs. UTR Read")
        
        qlModel.exposureData.addCallback(self._exposureDataCallback)
        qlModel.snrAxisRange.addCallback(self._snrAxisRangeCallback)
        qlModel.utrData.addCallback(self._utrDataCallback)
    
    def _exposureDataCallback(self, keyVar):
        """exposureData keyVar callback. Used to display the target S/N.
        """
        snrGoal = keyVar[5]
        if snrGoal is None or snrGoal <= 0:
            self.snrGoalLine.clear()
        else:
            self.snrGoalLine.show(snrGoal**2)
            
    def _snrAxisRangeCallback(self, keyVar):
        """snrAxisRange has been updated
        """
        if None in keyVar:
            return
        self.axes.set_ylim(keyVar[0]**2, keyVar[1]**2, auto=False)
        self.canvas.draw()

    def _utrDataCallback(self, keyVar):
        """utrData keyVar callback
        """
        if keyVar[0] is None:
            return
        self.utrReadDataList.addItem(DataObjects.UTRData(keyVar))
        dataList = self.utrReadDataList.getList()
        
        numList = [elt.readNum for elt in dataList]
        snrSqList = [elt.snr**2 for elt in dataList]
        estReads = None
        nReads = None
        fitCoeffs = None
        self.dataLine.set_data(numList, snrSqList)
        if numList:
            estReads = dataList[-1].numReadsToTarget
            nReads = dataList[-1].nReads
            fitCoeffs = dataList[-1].snrTotalLinFitCoeffs
            xMin = numList[0]
            xMax = max(numList[-1], estReads, nReads)
        else:
            xMin = 1
            xMax = 1
        xMin = xMin - 0.49
        xMax = xMax + 0.49
        self.axes.set_xlim(xMin, xMax)

        # show a horizontal line for the estimated number of reads, if present and > 0
        if estReads is None or estReads <= 0:
            self.estReadsLine.clear()
        else:
            self.estReadsLine.show(estReads)
            
        # code to draw fit line goes here.
        # dataList is empty then set line data to the empty list; otherwise:
        # evaluate fit over range xMin to xMax
        # set data and display it
        if fitCoeffs is None:
            fitReadNumArr = []
            fitSnrSqArr = []
        else:
            dx = (xMax - xMin) / 100.0
            fitReadNumArr = numpy.arange(xMin, xMax, dx)
            fitSnrSqArr = fitReadNumArr * fitCoeffs[1] + fitCoeffs[0]
#         print "fitCoeffs=", fitCoeffs
#         print "fitReadNumArr=", fitReadNumArr
#         print "fitSnrSqArr=", fitSnrSqArr
        self.fitLine.set_data(fitReadNumArr, fitSnrSqArr)

        self.canvas.draw()


if __name__ == '__main__':
    root = RO.Wdg.PythonTk()

    from . import TestData
    tuiModel = TestData.tuiModel

    testFrame = SNRGraphWdg(tuiModel.tkRoot, width=4, height=4)
    testFrame.pack(side="top", expand="yes")

    Tkinter.Button(text="Demo", command=TestData.animate).pack(side="top")

    TestData.start()

    tuiModel.reactor.run()
