#!/usr/local/bin/python
"""Allows specifying wrap preference for the azimuth and rotator axes.

To do: consider expanding help text to something like:
* Nearest: choose the wrap nearest the current position
* Negative: choose the wrap with the smaller angle
* Middle: choose the wrap nearest the center of rotation
* Positive: choose the wrap nearest the larger angle

History:
2001-11-05 ROwen    First version with history.
2002-06-25 ROwen    Removed an unneeded keyword from inputCont.
2002-07-31 ROwen    Modified to use the RO.CoordSys module.
2002-11-15 ROwen    added help; modified to use RO.Wdg.ROOptionMenu.
2003-03-11 ROwen    Switched from RO.Wdg.ROOptionMenu to RO.Wdg.OptionMenu.
2003-03-31 ROwen    Switched from RO.Wdg.LabelledWdg to RO.Wdg.Gridder.
2003-04-14 ROwen    Modified to use TUI.TCC.UserModel.
2003-05-28 ROwen    Modified to use InputCont ROEntry instead of TkWdg.
2003-06-12 ROwen    Added helpText.
2003-07-09 ROwen    Modified to use overhauled RO.InputCont.
2003-10-23 ROwen    Modified to allow abbreviations.
2003-10-24 ROwen    Added userModel input.
2004-05-18 ROwen    Stopped importing sys since it wasn't used.
2004-09-24 ROwen    Added a Defaults button.
2004-12-13 ROwen    Changed doEnable to setEnable for modified RO.InputCont.
"""
import Tkinter
import RO.CoordSys
import RO.InputCont
import RO.Wdg
import TUI.TCC.UserModel

_HelpURL = "Telescope/SlewWin/AxisWrapPanel.html"

class AxisWrapWdg(RO.Wdg.InputContFrame):
    """A widget showing wrap options.
    
    Inputs:
    - master        master Tk widget -- typically a frame or window
    - userModel     a TUI.TCC.UserModel; specify only if global model
                    not wanted (e.g. for checking catalog values)
    - defButtonText text for the restore defaults button;
                    None for no button;
                    "" for default label ("Defaults")
    - **kargs       keyword arguments for Tkinter.Frame
    """
    WrapOptions = ("Nearest", "Negative", "Middle", "Positive")
    def __init__ (self,
        master = None,
        userModel = None,
        defButtonText = None,
    **kargs):
        self.enable = True
        
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        
        Tkinter.Label(self, text="Axis Wrap").grid(row=0, columnspan=3)

        gr = RO.Wdg.Gridder(self, row=1, sticky="w")
        
        dataList = ( # axis name, label, keyword, default value
            ("Azimuth", "Az", "AzWrap", "Nearest"),
            ("Rotator", "Rot", "RotWrap", "Middle"),
        )
        
        self.wdgSet = []
        inputContList = []
        for axisName, wdgLabel, keyword, defValue in dataList:
            wdg = RO.Wdg.OptionMenu(self,
                items = AxisWrapWdg.WrapOptions,
                defValue = defValue,
                abbrevOK = True,
                ignoreCase = True,
                helpText = "%s axis wrap preference" % axisName,
                helpURL = _HelpURL,
            )
            self.wdgSet.append(wdg)
            gr.gridWdg (
                label = wdgLabel,
                dataWdg = wdg,
            )
            inputContList.append (
                RO.InputCont.WdgCont (
                    name = keyword,
                    wdgs = wdg,
                    formatFunc = RO.InputCont.VMSQualFmt(),
                ),
            )
        
        defButton = RO.Wdg.Button(self,
            text = "Defaults",
            command = self.restoreDefault,
            helpText = "Restore defaults",
        )
        gr.gridWdg(None, defButton)
        
        gr.allGridded()
        
        self.inputCont = RO.InputCont.ContList (
            conts = inputContList,
            formatFunc = RO.InputCont.BasicContListFmt(valSep=""),
        )
        
        # "restore defaults" button
        self.defaultButton = None
        if defButtonText == "":
            defButtonText = "Defaults"
        if defButtonText:
            self.defaultButton = Tkinter.Button(self,
                text=defButtonText,
                command=self.restoreDefault,
            ).grid(row=3, column=0, columnspan=3)

        self.inputCont.restoreDefault()

        userModel = TUI.TCC.UserModel.getModel()
        userModel.coordSysName.addCallback(self._coordSysChanged)
    
    def _coordSysChanged (self, coordSys):
        """Updates the display when the coordinate system is changed.
        """
        if coordSys == RO.CoordSys.Mount:
            self.setEnable(False)
        else:
            self.setEnable(True)

if __name__ == "__main__":
    import CoordSysWdg

    root = RO.Wdg.PythonTk()

    def printOptions():
        print optFrame.getString()

    csysWdg = CoordSysWdg.CoordSysWdg(root)
    
    getButton = Tkinter.Button (root, command=printOptions, text="Print Options")
    
    optFrame = AxisWrapWdg(root,
        defButtonText = "",
    )
    
    csysWdg.pack()
    getButton.pack()
    optFrame.pack()

    root.mainloop()
