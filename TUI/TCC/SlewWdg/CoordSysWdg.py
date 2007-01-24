#!/usr/bin/env python
"""Widget to allow users to specify a target position and initiate a slew.

History:
2002-06-25 ROwen    First version with history.
2002-07-29 ROwen    List FK5 before FK4, show epoch with 1 decimal point.
2002-07-31 ROwen    Modified to use the RO.CoordSys module.
2002-08-02 ROwen    Mod. coordsys menu to take focus and have a separator.
2002-11-15 ROwen    modified to use ROOptionMenu and added help
2002-11-26 ROwen    modified to use URL-based help.
2003-03-11 ROwen    Changed to use OptionMenu instead of ROOptionMenu.
2003-04-09 ROwen    Added helpURL to the date input widget.
2003-04-14 ROwen    Modified to use TUI.TCC.UserModel.
2003-04-28 ROwen    Removed getDateVar; use UserModel instead.
2003-05-09 ROwen    Use improved RO.CoordSys.
2003-06-12 ROwen    Added helpText for each coordinate system.
2003-07-09 ROwen    Modified to use overhauled RO.InputCont.
2003-10-14 ROwen    Fixed helpText for ICRS (was unicode and so did not display).
2003-10-17 ROwen    Separated CSys and Date in the input container
                    to help upcoming user catalogs.
2003-10-23 ROwen    Modified to allow abbreviations.
2003-10-28 ROwen    Added userModel input.
2003-11-04 ROwen    Changed default from ICRS to FK5.
2003-12-05 ROwen    Modified for RO.Wdg changes.
2005-06-07 ROwen    Fixed a (normally commented-out) diagnostic print statement.
"""
import Tkinter
import RO.InputCont
import RO.StringUtil
import RO.Wdg
import RO.CoordSys
import TUI.TCC.UserModel

_HelpURL = "Telescope/CoordSys.html"

_CoordSysMenuItems = (
    RO.CoordSys.ICRS,
    RO.CoordSys.FK5,
    RO.CoordSys.FK4,
    RO.CoordSys.Galactic,
    RO.CoordSys.Geocentric,
    None,
    RO.CoordSys.Topocentric,
    RO.CoordSys.Observed,
#   RO.CoordSys.Physical,
    RO.CoordSys.Mount,
)
_CoordSysHelpDict = {
    RO.CoordSys.ICRS: "ICRS (FK5 J2000) mean RA/Dec: the current standard",
    RO.CoordSys.FK5: "FK5 mean RA/Dec: the IAU 1976 standard",
    RO.CoordSys.FK4: "FK4 mean RA/Dec: an old standard",
    RO.CoordSys.Galactic: "Galactic long/lat: the IAU 1958 standard",
    RO.CoordSys.Geocentric: "Current apparent geocentric RA/Dec",
    RO.CoordSys.Topocentric: "Current apparent topocentric az/alt; no refraction corr.",
    RO.CoordSys.Observed: "Observed az/alt: topocentric plus refraction correction",
    RO.CoordSys.Physical: "Physical az/alt; pos. of a perfect telescope",
    RO.CoordSys.Mount: "Mount az/alt: pos. sent to the axis controllers; no wrap",

}

class CoordSysWdg (RO.Wdg.InputContFrame):
    def __init__ (self,
        master = None,
        userModel = None,
     **kargs):
        """Creates a new widget for specifying coordinate systems.
        
        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        
        userModel = userModel or TUI.TCC.UserModel.getModel()

        # coordinate system menu
        self.coordSysMenu = RO.Wdg.OptionMenu (self,
            var = userModel.coordSysName.getVar(),
            defValue = "FK5",
            items = _CoordSysMenuItems,
            abbrevOK = True,
            ignoreCase = True,
            helpText = [_CoordSysHelpDict.get(item) for item in _CoordSysMenuItems],
            helpURL = _HelpURL,
        )
        self.coordSysMenu.pack(side="left")

        # date
        self.dateFrame = Tkinter.Frame(self)
        self.dateEntryWdg = RO.Wdg.FloatEntry(
            master = self.dateFrame,
            var = userModel.coordSysDate.getVar(),
            minValue =    0.0,
            maxValue = 3000.0,
            defValue = None,
            defFormat = "%.1f",
            helpText = "Date of equinox (and of observation, for proper motion correction)",
            helpURL = _HelpURL,
            width = 6,
        )
        self.dateLabel = Tkinter.Label(self.dateFrame, justify="right")
        self.dateLabel.pack(side="left", anchor="w")
        self.dateEntryWdg.pack(side="left", anchor="w")
        self.dateShown = False
        
        # set up format function and input container
        def formatCSysDate(inputCont):
            csys, date = inputCont.getValueList()
            defCSys, defDate = inputCont.getDefValueList()
            if date not in ("", defDate):
                return csys + "=" + date
            else:
                return csys

        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = "CSys",
                    wdgs = self.coordSysMenu,
                    omitDef = False,
                ),
                RO.InputCont.WdgCont (
                    name = "Date",
                    wdgs = self.dateEntryWdg,
                    omitDef = False,
                ),
            ],
            formatFunc = formatCSysDate,
        )

        userModel.coordSysName.addCallback(self._coordSysChanged)

        # set default values
        self.restoreDefault()
        
    def _coordSysChanged (self, coordSys):
        """Update the display when the coordinate system is changed.
        """
#       print "CoordSysWdg._coordSysChanged(coordSys=%r)" % (coordSys,)
        sysConst = RO.CoordSys.getSysConst(coordSys)
        if sysConst.hasEquinox():
            self.dateLabel["text"] = sysConst.datePrefix()
            self.dateEntryWdg.setDefault(sysConst.defaultDate())
            if not self.dateShown:
                self.dateFrame.pack(side="left")
            self.dateShown = True
        else:
            self.dateFrame.pack_forget()
            self.dateEntryWdg.setDefault(None)
            self.dateShown = False
        self.dateEntryWdg.restoreDefault()

if __name__ == "__main__":
    root = RO.Wdg.PythonTk()

    testFrame = CoordSysWdg()
    testFrame.pack()

    def printCommand():
        print testFrame.getString()

    def printValueDict():
        print testFrame.getValueDict()

    strButton = Tkinter.Button (root, command=printCommand, text="Print Command")
    strButton.pack()

    vdButton = Tkinter.Button (root, command=printValueDict, text="Print Value Dict")
    vdButton.pack()

    root.mainloop()
