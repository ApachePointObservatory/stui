#!/usr/local/bin/python
"""A container that scrolls a widget.

History:
2003-12-16 ROwen
2004-08-11 ROwen    Define __all__ to restrict import.
2004-09-14 ROwen    Tweaked the import in the test code.
2004-11-22 ROwen    Corrected doc string for ScrolledWdg.
"""
__all__ = ['ScrolledWdg']

import Tkinter

class ScrolledWdg(Tkinter.Frame):
    """Scroll a widget such as a frame.
    
    Due to quirks in tk or Tkinter this requires three steps:
    - Create the ScrolledWdg
    - Create the widget to be scrolled, using getWdgParent() as the parent
    - Set the widget using setWdg()
    
    Inputs:
    - master    master widget
    - hscroll   scroll horizontally?
                if not, frame will try to resize in width to show all
    - vscroll   scroll vertically?
                if not, frame will try to resize in height to show all
    - height    minimum height for widget
    extra keyword arguments are for Tkinter.Frame.
    """

    def __init__ (self,
        master,
        hscroll = False,
        vscroll = True,
        height = 0,
    **kargs):
        
        Tkinter.Frame.__init__(self, master, **kargs)
        
        self._hscroll = bool(hscroll)
        self._vscroll = bool(vscroll)
        self._wdg = None
        self._hincr = None
        self._vincr = None

        # create the canvas
        self._cnv = Tkinter.Canvas(self, height=height)
        self._cnv.grid(row=0, column=0, sticky="nsew")
        
        # create the scrollbars and connect them up
        if hscroll:
            hsb = Tkinter.Scrollbar(self, orient="horizontal", command=self._cnv.xview)
            self._cnv.configure(xscrollcommand = hsb.set)
            hsb.grid(row=1, column=0, sticky="ew")
        else:
            hsb = None
        self._hscrollbar = hsb
        
        if vscroll:
            vsb = Tkinter.Scrollbar(self, orient="vertical", command=self._cnv.yview)
            self._cnv.configure(yscrollcommand = vsb.set)
            vsb.grid(row=0, column=1, sticky="ns")
        else:
            vsb = None
        self._vscrollbar = vsb
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def getWdgParent(self):
        """Return the object you should use as your widget's parent.
        """
        return self._cnv
        
    def setWdg(self,
        wdg,
        hincr = None,
        vincr = None,
    ):
        """Specify the widget to scroll and optional increment info.
        
        Inputs:
        - wdg       the widget to scroll
        - hincr     horizontal scroll increment; one of:
                    - None, no increment
                    - an integer: increment size in pixels
                    - a widget: requested width is the size
                    ignored if hscroll false
        - vincr     vertical scroll increment; see hincr for details;
                    may be the same widget as hincr;
                    ignored if vscroll false
        
        Raises RuntimeError if called more than once.
        """
        if self._wdg != None:
            raise RuntimeError("setWdg may only be called once")

        self._wdg = wdg
        self._hincr = hincr
        self._vincr = vincr

        # add the widget to the canvas
        self._cnv.create_window(0, 0,
            anchor="nw",
            window=self._wdg,
        )
        self._cnv.grid(row=0, column=0, sticky="nsew")
        
        # deal with increments
        if self._hincr != None:
            if hasattr(self._hincr, "bind"):
                self._hincr.bind("<Configure>", self._configHIncr, add=True)
                self._configHIncr()
            else:
                self._cnv.configure(xscrollincr = self._hincr)
        if self._vincr != None:
            if hasattr(self._vincr, "bind"):
                self._vincr.bind("<Configure>", self._configVIncr, add=True)
                self._configVIncr()
            else:
                self._cnv.configure(yscrollincr = self._vincr)
        
        # set up bindings to track changes in sizes of widgets
        self._wdg.bind("<Configure>", self._configWdg)
        self._configWdg()
    
    def _configWdg(self, evt=None):
        """Called when wdg changes size.
        """
#       print "ScrolledWdg._configWdg called"
        reqwidth = self._wdg.winfo_reqwidth()
        reqheight = self._wdg.winfo_reqheight()
        self._cnv.configure(
            scrollregion = (0, 0, reqwidth, reqheight),
        )
        if not self._hscrollbar:
            self._cnv.configure(
                width = reqwidth,
            )
        if not self._vscrollbar:
            self._cnv.configure(
                height = reqheight,
            )
        
    def _configHIncr(self, evt=None):
        """Called when the hincr widget changes size.
        """
        width = max(self._hincr.winfo_reqwidth(), self._hincr.winfo_width())
        self._cnv.configure(xscrollincr = width)
#       print "ScrolledWdg._configHIncr; xscrollincr =", self._cnv["xscrollincr"]
        
    def _configVIncr(self, evt=None):
        """Called when the vincr widget changes size.
        """
        height = max(self._vincr.winfo_reqheight(), self._vincr.winfo_height())
        self._cnv.configure(yscrollincr = height)
#       print "ScrolledWdg._configVIncr; yscrollincr =", self._cnv["yscrollincr"]


if __name__ == '__main__':
    import PythonTk
    root = PythonTk.PythonTk()
    
    root.resizable(False, True)
    
    NRows = 20
    NCol = 10
    
    scFrame = ScrolledWdg(
        master = root,
        hscroll = False,
        vscroll = True,
    )

    labelDict = {}
    testFrame = Tkinter.Frame(scFrame.getWdgParent())
    for row in range(NRows):
        for col in range(NCol):
            ind = (row, col)
            label = Tkinter.Label(testFrame, text="%s" % (ind,))
            label.grid(row = row, column=col)
            labelDict[ind] = label
    
    scFrame.setWdg(
        wdg = testFrame,
        vincr = labelDict[(0,0)],
    )
    scFrame.pack(expand=True, fill="both")

    root.mainloop()
