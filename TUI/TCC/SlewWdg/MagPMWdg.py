#!/usr/bin/env python
"""Allows entry of magnitude and proper motion.

History:
2001-11-05 ROwen    First version with history.
2002-06-25 ROwen    Removed an unneeded keyword from inputCont.
2002-07-31 ROwen    Modified to use the RO.CoordSys module.
2002-11-15 ROwen    Added help for ObsDate, PM and RadVel.
2002-11-26 ROwen    Changed to URL help and added help for all widgets.
2003-03-31 ROwen    Changed to use RO.Wdg.Gridder instead of LabelledWdg.
2003-04-14 ROwen    Modified to use TUI.TCC.UserModel.
2003-04-18 ROwen    Commented out the radial velocity control; it has no practical use.
2003-06-16 ROwen    Bug fix: units wrong for PM2.
2003-07-10 ROwen    Major overhaul; modified to use overhauled RO.InputCont.
2003-10-16 ROwen    Changed Magnitude to Mag in data dict
                    to simplify user catalogs.
2003-10-24 ROwen    Added userModel input; re-added Rv; and lengthened
                    Mag to Magnitude to make catalogs easier.
2003-11-04 ROwen    Modified to show self if set non-default.
2005-08-15 ROwen    Fixed PR 240: Distance was ignored (because it was not in self.inputCont).
2007-08-09 ROwen    Moved coordsys-based enable/disable to a parent widget.
"""
import Tkinter
import RO.CoordSys
import RO.InputCont
import RO.StringUtil
import RO.Wdg
import TUI.TCC.UserModel

_HelpPrefix = "Telescope/SlewWin/MagPMPanel.html#"

_EntryWidth = 6

_DateHelpNoEquinox = "Date of observation (for proper motion correction)"
_DateHelpWithEquinox = "Date of observation (for PM correction) and of equinox"

class MagPMWdg(RO.Wdg.InputContFrame):
    """A widget for specifying magnitude,
    proper motion and parallax (or distance).
    The exact set of controls depends on the coordinate system.

    Inputs:
    - master        master Tk widget -- typically a frame or window
    - userModel     a TUI.TCC.UserModel; specify only if global model
                    not wanted (e.g. for checking catalog values)
    - **kargs       keyword arguments for Tkinter.Frame
    """
    def __init__ (self,
        master,
        userModel = None,
    **kargs):
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        
        userModel = userModel or TUI.TCC.UserModel.getModel()
        dateVar = userModel.coordSysDate.getVar()
        
        self.cat = None

        self.gr = RO.Wdg.Gridder(self)
        
        self.gr.gridWdg (
            label = False,
            dataWdg = Tkinter.Label(self, text="Mag, PM"),
            colSpan = 3,
            sticky="",
        )
        
        self.magWdg = self.gr.gridWdg (
            label = "Magnitude",
            dataWdg = RO.Wdg.FloatEntry (self,
                -999, 999,
                width = _EntryWidth,
                helpText = "Magnitude of object",
                helpURL = _HelpPrefix + "Magnitude",
            ),
            cat = ("mean", "geo"),
        )
        self.dateWdg = self.gr.gridWdg (
            label = "Obs Date",
            dataWdg = RO.Wdg.FloatEntry (self,
                -9.9e99, 9.9e99,
                width = _EntryWidth,
                var=dateVar,
                helpURL = _HelpPrefix + "ObsDate",
                helpText = _DateHelpNoEquinox,
            ),
            cat = "mean",
        )
        self.pm1Wdg = self.gr.gridWdg (
            label = "PM RA",
            dataWdg = RO.Wdg.FloatEntry (self,
                -9.9e99, 9.9e99,
                width = _EntryWidth,
                helpURL = _HelpPrefix + "PM1",
            ),
            units = 's/cent',
            cat = "mean",
        )
        self.pm2Wdg = self.gr.gridWdg (
            label = "PM Dec",
            dataWdg = RO.Wdg.FloatEntry (self,
                -9.9e99, 9.9e99,
                helpURL = _HelpPrefix + "PM2",
                width = _EntryWidth,
            ),
            units = '"/cent',
            cat = "mean",
        )
        self.parallaxWdg = self.gr.gridWdg (
            label = "Parallax",
            dataWdg = RO.Wdg.FloatEntry (self,
                0.0, 9.9e99,
                helpText = "Parallax of object",
                helpURL = _HelpPrefix + "Parallax",
                width = _EntryWidth,
            ),
            units = '"',
            cat = "mean",
        )
        self.radVelWdg = self.gr.gridWdg (
            label = "Rad Vel",
            dataWdg = RO.Wdg.FloatEntry (self,
                -9.9e99, 9.9e99,
                helpURL = _HelpPrefix + "RadVel",
                helpText = "Redial velocity, positive receding",
                    width = _EntryWidth,
            ),
            units = 'km/s',
            cat = "mean",
        )
        self.distWdg = self.gr.gridWdg (
            label = "Distance",
            dataWdg = RO.Wdg.FloatEntry (self,
                0.0, 9.9e99,
                helpText = "Distance to object (blank for infinity)",
                helpURL = _HelpPrefix + "Distance",
                    width = _EntryWidth,
            ),
            units = 'parsecs',
            cat = "geo",
        )

        def blankToZero(astr):
            if astr == '':
                return '0'
            return astr

        self.inputCont = RO.InputCont.ContList (
            conts = (
                RO.InputCont.WdgCont (
                    name = "Magnitude",
                    wdgs = self.magWdg.dataWdg,
                    formatFunc = RO.InputCont.VMSQualFmt(),
                ),
                RO.InputCont.WdgCont (
                    name = "PM",
                    wdgs = (self.pm1Wdg.dataWdg, self.pm2Wdg.dataWdg),
                    formatFunc = RO.InputCont.VMSQualFmt(
                        valFmt = blankToZero,
                    ),
                ),
                RO.InputCont.WdgCont (
                    name = "Px",
                    wdgs = self.parallaxWdg.dataWdg,
                    formatFunc = RO.InputCont.VMSQualFmt(),
                ),
                RO.InputCont.WdgCont (
                    name = "Distance",
                    wdgs = self.distWdg.dataWdg,
                    formatFunc = RO.InputCont.VMSQualFmt(),
                ),
                RO.InputCont.WdgCont (
                    name = "Rv",
                    wdgs = self.radVelWdg.dataWdg,
                    formatFunc = RO.InputCont.VMSQualFmt(),
                ),
            ),
            formatFunc = RO.InputCont.BasicContListFmt(valSep = ""),
        )
        
        expandRow = self.gr.getNextRow()
        self.rowconfigure(expandRow, weight=1)
        
        defButtonWdg = RO.Wdg.Button(self,
                text="Defaults",
                command=self.restoreDefault,
                helpText = "Restore defaults",
            )
        self.gr.gridWdg(
            label = False,
            dataWdg = defButtonWdg,
            colSpan = 3,
            sticky = "",
            row = expandRow + 1,
            cat = ("mean", "geo"),
        )
    
    def _coordSysChanged (self, coordSys):
        """Update the display when the coordinate system is changed.
        """
        coordSysConst = RO.CoordSys.getSysConst(coordSys)
        
        if coordSysConst.isMean():
            cat = "mean"
            if coordSysConst.hasEquinox():
                for wdg in self.dateWdg.wdgSet:
                    wdg.helpText = _DateHelpWithEquinox
            else:
                for wdg in self.dateWdg.wdgSet:
                    wdg.helpText = _DateHelpNoEquinox
            posLabels = coordSysConst.posLabels()
            self.pm1Wdg.labelWdg["text"] = "PM %s" % posLabels[0]
            self.pm1Wdg.dataWdg.helpText = "Proper motion in %s (d%s/dt, i.e. larger near the pole)" % (posLabels[0], posLabels[0])
            self.pm2Wdg.labelWdg["text"] = "PM %s" % posLabels[1]
            self.pm2Wdg.dataWdg.helpText = "Proper motion in %s" % posLabels[1]
        elif coordSysConst.name() == RO.CoordSys.Geocentric:
            cat = "geo"
        else:
            cat = ""
            
        if cat != self.cat:
            self.cat = cat
#           print "showing category", cat
            for wdg, catList in self.gr._showHideWdgDict.iteritems():
#               print "processing wdg=%r, caList=%r" % (wdg, catList)
                if cat not in catList:
                    wdg.grid_remove()
                else:
                    wdg.grid()
            self.parallaxWdg.dataWdg.clear()
            self.distWdg.dataWdg.clear()
        

if __name__ == "__main__":
    import CoordSysWdg

    root = RO.Wdg.PythonTk()

    def printOptions():
        print magWdgSet.getString()
        
    def clear():
        magWdgSet.clear()
        
    getButton = Tkinter.Button (root, command=printOptions, text="Print Options")
    getButton.pack()
        
    getButton = Tkinter.Button (root, command=clear, text="Clear")
    getButton.pack()
        
    magWdgSet = MagPMWdg(root)
    magWdgSet.pack()

    root.mainloop()
