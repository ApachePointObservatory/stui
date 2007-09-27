#!/usr/bin/env python
"""A widget showing options for the /pterr calibration qualifier
of the track command.

History:
2002-07-31 ROwen    Modified to use the RO.CoordSys module.
2002-12-04 ROwen    Added helpURL support.
2002-12-23 ROwen    Bug fix: failed if coordSysVar not specified;
                    exposed by pychecker.
2003-04-14 ROwen    Modified to use TUI.TCC.UserModel.
2003-04-28 ROwen    Bug fix: test code used CoordSysWdg.getCoordSysVar.
2003-07-09 ROwen    Modified to use overhauled RO.InputCont.
2003-10-17 ROwen    Changed PtErr to PtError.
2003-10-24 ROwen    Added userModel input.
2004-04-19 ROwen    Bug fixes: was not sending calibrate command
                    if panel showing but all options were default;
                    also was sending FindRefStar instead of FindReference.
2004-12-13 ROwen    Changed doEanble to setEnable for modified RO.InputCont.
2007-08-09 ROwen    Moved coordsys-based enable/disable to a parent widget.
2007-09-27 ROwen    Removed unused userModel input (thanks, pychecker).
"""
import RO.CoordSys
import RO.Wdg
import RO.InputCont

_HelpURL = "Telescope/SlewWin/CalibratePanel.html#"

class CalibWdg(RO.Wdg.OptionButtons):
    """A widget showing calibration options.
    
    Inputs:
    - master        master Tk widget -- typically a frame or window
    - **kargs       keyword arguments for Tkinter.Frame
    """
    def __init__ (self,
        master=None,
        **kargs
    ):
        RO.Wdg.OptionButtons.__init__(self, master,
            name = "PtError",
            optionList = (
                ("FindReference", "Find Ref Star", 1,
                    "Search position reference catalog for nearest star"),
                ("RefSlew", "Slew to Ref", 1,
                    "Slew telescope to position the reference star on the guide camera"),
                ("Correct", "Correct Error", 1,
                    "Measure pointing error and apply the correction"),
                ("Log", "Log Error", 0,
                    "Measure pointing error and log it to a file"),
                ("ObjSlew", "Slew to Object", 1,
                    "After doing everything else, slew to the specified object"),
            ),
            helpURLPrefix = _HelpURL,
            headerText = "Calibrate",
            defButton = True,
            formatFunc = RO.InputCont.VMSQualFmt(),
            omitDef = False,
            **kargs
        )


if __name__ == "__main__":
    import Tkinter
    import CoordSysWdg

    def doPrint():
        print optFrame.getString()
        
    root = RO.Wdg.PythonTk()
    csysWdg = CoordSysWdg.CoordSysWdg(root)
    csysWdg.pack(side="top", anchor="nw")
    
    optFrame = CalibWdg(root)
    
    optFrame.pack(side="top", anchor="nw")
    
    qualButton = Tkinter.Button (root, command=doPrint, text="Print")
    qualButton.pack()

    root.mainloop()
