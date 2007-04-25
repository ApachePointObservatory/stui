#!/usr/bin/env python
"""Widget to display and set an image subframe.

Known issues:
- stipple doesn't work for canvas rectangles on Aqua Tcl/Tk (8.4.11)
  so the default subframe is displayed on top with no fill.
- rectangles are displayed one pixel too high on Aqua Tcl/Tk (8.4.11)
  it's purely cosmetic so just live with it

History:
2006-09-14 ROwen
2006-09-26 ROwen    Added bin factor support to allow isCurrent
                    and full frame determinations to be binned.
2007-04-24 ROwen    Modified to use numpy instead of numarray.
"""
import Tkinter
import numpy
import RO.AddCallback
import RO.Wdg
import SubFrame

OutlineRectConfig = dict(
    outline = "black",
)
UnmodRectConfig = dict(
    outline = "black",
    fill = "gray",
#   stipple = "gray25", # ignored on MacOS X/Aqua tk
)
ModRectConfig = dict(
    outline = "red",
    fill = "pink",
#   stipple = "gray25", # ignored on MacOS X/Aqua tk
)

class SubFrameWdg(Tkinter.Frame, RO.AddCallback.BaseMixin, RO.Wdg.CtxMenuMixin):
    def __init__(self,
        master,
        subFrame = None,
        defSubFrame = None,
        callFunc = None,
        helpText = None,
        helpURL = None,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)
        RO.AddCallback.BaseMixin.__init__(self)
        RO.Wdg.CtxMenuMixin.__init__(self,
            helpURL = helpURL,
        )
        
        self.currRectCoords = []
        
        self.binFac = SubFrame.binFacAsArr(1)
    
        self.fullSize = None
        self.widthOverHeight = None
        self.redrawingRect = False
        
        self.subFrame = None
        self.defSubFrame = None

        self.subResRect = None # None or an RO.Wdg.ResizableRect
        self.defRectID = None # None or ID of a canvas rectangle
        
        cnvHeight = kargs.get("height", 100) - \
            2 * (self["borderwidth"] + self["highlightthickness"])
        
        self.cnv = Tkinter.Canvas(
            self,
            height = cnvHeight,
            width = 1, # start with this dimension and correct for image size
            selectborderwidth = 0,
            highlightthickness = 0,
            borderwidth = 0,
        )
        self.cnv.pack(expand = True, fill = "both") 
        self.cnv.bind("<Configure>", self._setCnvSize)
        self.cnv.bind("<Map>", self._setCnvSize)
        if helpText:
            self.cnv.helpText = helpText

        if subFrame:
            self.setSubFrame(subFrame)

        if defSubFrame:
            self.setDefSubFrame(defSubFrame)
        
        if callFunc:
            self.addCallback(callFunc)
    
    def begSizeFromRectCoords(self, rectCoords):
        """Convert coordinates of displayed rectangle
        to unbinned subframe beginning and size
        """
        if self.fullSize == None:
            return None

        floatMaxRectSize = numpy.array(self.getMaxCoords(), dtype=numpy.float) + (1.0, 1.0)
        floatFullSize = numpy.array(self.fullSize, dtype=numpy.float)

        rectBeg = numpy.array(rectCoords[0:2], dtype=numpy.float)
        rectEnd = numpy.array(rectCoords[2:4], dtype=numpy.float)
        rectSize = rectEnd  + [1.0, 1.0] - rectBeg

        # flip y axis to go from canvas coords with y=0 at top
        # to array coords with y=0 at bottom
        fracBeg = numpy.zeros(dtype=numpy.float).reshape([2])
        fracBeg[0] = rectBeg[0] / floatMaxRectSize[0]
        fracBeg[1] = 1.0 - ((rectEnd[1] + 1) / floatMaxRectSize[1])
        fracSize = rectSize / floatMaxRectSize
        
        subBeg = numpy.array(numpy.around(fracBeg * floatFullSize), dtype=numpy.int)
        subSize = numpy.array(numpy.around(fracSize * floatFullSize), dtype=numpy.int)
#       print "begSizeFromRectCoords(%s): maxRectSize=%s; fullSize=%s\n  rectBeg=%s, rectEnd=%s, rectSize=%s; fracBeg=%s, fracSize=%s\n  subBeg=%s, subEnd=%s" % \
#           (rectCoords, floatMaxRectSize, floatFullSize, rectBeg, rectEnd, rectSize, fracBeg, fracSize, subBeg, subEnd)
        return (subBeg, subSize)

    def getIsCurrent(self):
        """Return True if subFrame and default subFrame
        are equal at the current bin factor,
        or if both subFrame and subFrame are None.
        """
        if None in (self.subFrame, self.defSubFrame):
            return self.subFrame == self.defSubFrame
        
        return self.subFrame.isEqualBinned(self.binFac, self.defSubFrame)
    
    def getMaxCoords(self):
        """Return maximum coordinates of canvas."""
        return (self.cnv.winfo_width() - 1, self.cnv.winfo_height() - 1)
    
    def sameSubFrame(self, sf):
        """Return True if sf matches current subframe with current bin factor
        or if self.subFrame and sf are both None.
        """
        if self.subFrame == None:
            return self.subFrame == sf

        return self.subFrame.isEqualBinned(self.binFac, sf)
    
    def isFullFrame(self):
        """Return True if subFrame is full frame at the current bin factor.
        """
        if self.subFrame == None:
            return False
        
        return self.subFrame.isFullFrameBinned(self.binFac)
    
    def rectCoordsFromBegSize(self, subBeg, subSize):
        """Convert unbinned subframe beginning and size
        to coordinates of the displayed rectangle.
        """
        if self.fullSize == None:
            return None

        floatMaxRectSize = numpy.array(self.getMaxCoords(), dtype=numpy.float) + (1.0, 1.0)
        floatFullSize = numpy.array(self.fullSize, dtype=numpy.float)
        
        subEnd = numpy.add(subBeg, subSize) - 1
        
        # flip y axis to go from array coords with y=0 at bottom
        # to canvas coords with y=0 at top
        fracBeg = numpy.zeros(dtype=numpy.float).reshape([2])
        fracBeg[0] = subBeg[0] / floatFullSize[0]
        fracBeg[1] = 1.0 - ((subEnd[1] + 1) / floatFullSize[1])
        fracSize = numpy.divide(subSize, floatFullSize)
        
        floatRectBeg = fracBeg * floatMaxRectSize
        floatRectSize = fracSize * floatMaxRectSize
        floatRectEnd = floatRectBeg + floatRectSize - [1.0, 1.0]

        rectBeg = numpy.array(numpy.around(floatRectBeg), dtype=numpy.int)
        rectEnd = numpy.array(numpy.around(floatRectEnd), dtype=numpy.int)
#       print "rectCoordsFromBegSize(subBeg=%s, subSize=%s): maxRectSize=%s; fullSize=%s\n  subEnd=%s, fracBeg=%s, fracSize=%s; rectBeg=%s, rectEnd=%s" % \
#           (subBeg, subSize, floatMaxRectSize, floatFullSize, subEnd, fracBeg, fracSize, rectBeg, rectEnd)
        return (rectBeg[0], rectBeg[1], rectEnd[0], rectEnd[1])
    
    def restoreDefault(self):
        self.setSubFrame(self.defSubFrame)
    
    def setBinFac(self, binFac):
        """Set bin factor.
        """
        self.binFac = SubFrame.binFacAsArr(binFac)
        self.update()
    
    def setDefSubFrame(self, defSubFrame):
        """Set the default subFrame.
        
        defSubFrame may be a SubFrame object or None;
        in the latter case no default rectangle is displayed.
        """
#       print "defSetSubFrame(%s)" % (defSubFrame,)
        if defSubFrame:
            self.defSubFrame = defSubFrame.copy()
            if not self.defRectID:
                self.defRectID = self.cnv.create_rectangle(
                    0, 0, 0, 0,
                    width = 1,
                **OutlineRectConfig)
        else:
            self.defSubFrame = None
            if self.defRectID:
                self.cnv.delete(self.defRectID)
                self.defRectID = None
        
        self.update()
    
    def setFullFrame(self):
        """Set subFrame to full frame (if subFrame exists).
        """
        if not self.subFrame:
            return
        self.subFrame.setFullFrame()
        self.update()
    
    def setSubFrame(self, subFrame):
        """Set the subframe.

        subFrame may be a SubFrame object or None;
        in the latter case no subFrame rectangle is displayed.
        """
#       print "setSubFrame(%s)" % (subFrame,)
        if subFrame:
            newFullSize = (self.subFrame == None) or not numpy.alltrue(subFrame.fullSize == self.subFrame.fullSize)
            self.subFrame = subFrame.copy()
            
            if not self.subResRect:
                self.subResRect = RO.Wdg.ResizableRect(
                    self.cnv,
                    0, 0, 0, 0,
                    callFunc = self._subResRectCallback,
                **UnmodRectConfig)
        else:
            newFullSize = False
            self.subFrame = None

            if self.subResRect:
                self.subResRect.delete()
                self.subResRect = None

        if newFullSize:
            self.fullSize = self.subFrame.fullSize
            self.widthOverHeight = float(self.fullSize[0]) / float(self.fullSize[1])
            self._setCnvSize()
        else:
            self._redrawRects()

        self._doCallbacks()
    
    def update(self):
        self._redrawRects()
        self._doCallbacks()

    def _subResRectCallback(self, rect=None):
        """Called when subframe rectangle changes.
        
        If the change is due to the user dragging it around,
        then update subFrame accordingly.
        """
        if self.redrawingRect:
            # rect is being changed by local code to match subFrame changes;
            # nothing to do
            return

        # subResRect is being changed by user; update subFrame accordingly
        newCoords = self.subResRect.getCoords()
        if newCoords == self.currRectCoords:
            return
        
        self.currRectCoords = newCoords
            
        # update self.subFrame
        newBeg, newSize = self.begSizeFromRectCoords(newCoords)
        self.subFrame.setSubBegSize(newBeg, newSize)
        
        self._stateChanged()
    
    def _stateChanged(self):
        """Call whenever either the state has changed."""
        if self.subResRect:
            if self.getIsCurrent():
                self.cnv.itemconfigure(self.subResRect.rectID, **UnmodRectConfig)
            else:
                self.cnv.itemconfigure(self.subResRect.rectID, **ModRectConfig)
        self._doCallbacks()
    
    def _redrawRects(self):     
        try:
            self.redrawingRect = True

            # set default rectangle
            if self.defSubFrame:
                if self.defRectID == None:
                    raise RuntimeError("have defSubFrame but no defRectID")
                subBeg, subSize = self.defSubFrame.getSubBegSize()
                rectCoords = self.rectCoordsFromBegSize(subBeg, subSize)
                self.cnv.coords(self.defRectID, *rectCoords)
            elif self.defRectID != None:
                raise RuntimeError("have defRectID but no defSubFrame")
            
            # set current rectangle
            if self.subFrame:
                subBeg, subSize = self.subFrame.getSubBegSize()
                rectCoords = self.rectCoordsFromBegSize(subBeg, subSize)
    #           print "cnv width=%s; height=%s; subBeg=%s, subSize=%s, rectCoords=%s" % \
    #               (self.cnv.winfo_width(), self.cnv.winfo_height(), subBeg, subSize, rectCoords)
                self.subResRect.setCoords(*rectCoords)
        finally:
            self.redrawingRect = False
        
        self._stateChanged()
        
    def _setCnvSize(self, evt=None):
        """Set window canvas width based on displayed height
        and on proportions of the camera CCD.
        """
        if not self.cnv.winfo_ismapped():
            #print "_setCnvSize(): not mapped"
            return
        
        height = int(self.cnv.winfo_height())
        newWidth = int(round(height * self.widthOverHeight))
        self.cnv["width"] = newWidth
        #print "_setCnvSize(): height=%s, new width=%s" % (height, newWidth)
        
        self._redrawRects()
    

if __name__ == "__main__":
    root = Tkinter.Tk()
    
    def printSubFrame(sf):
        if not sf.subFrame:
            return
        subBeg, subSize = sf.subFrame.getSubBegSize()
        print "subBeg=%s, %s; subSize=%s, %s" % (subBeg[0], subBeg[1], subSize[0], subSize[1])
    
    subFrame = SubFrame.SubFrame(
            fullSize = (512, 512),
            subBeg = (128, 128),
            subSize = (256, 256),
        )
    
    sfw = SubFrameWdg(
        master = root,
        subFrame = subFrame,
        defSubFrame = subFrame,
        helpText = "Sample SubFrame Wdg",
        callFunc = printSubFrame,
        width = 200,
        height = 200,
        borderwidth = 2,
        relief = "solid",
    )
    sfw.grid(row=0, column=0, sticky="ns")
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    
    def delDefault():
        sfw.setDefSubFrame(None)
    
    def setDefault():
        sfw.setDefSubFrame(subFrame)
    
    def delSubFrame():
        sfw.setSubFrame(None)
    
    def setSubFrame():
        sfw.setSubFrame(subFrame)
    
    btnFrame = Tkinter.Frame(root)
    
    Tkinter.Button(btnFrame, text="Restore Default", command=sfw.restoreDefault).pack()
    Tkinter.Button(btnFrame, text="Full Frame", command = sfw.setFullFrame).pack()
    Tkinter.Button(btnFrame, text="Replace Default", command = setDefault).pack()
    Tkinter.Button(btnFrame, text="Delete Default", command = delDefault).pack()
    Tkinter.Button(btnFrame, text="Replace SubFrame", command = setSubFrame).pack()
    Tkinter.Button(btnFrame, text="Delete SubFrame", command = delSubFrame).pack()
    btnFrame.grid(row=1, column=0, sticky="ew")
    
    root.mainloop()
