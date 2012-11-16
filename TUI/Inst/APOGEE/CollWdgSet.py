#!/usr/bin/env python
"""APOGEE Collimator control and status

History:
2011-05-04 ROwen
2011-05-06 ROwen    Bug fix: commands were missing the verb "coll".
2011-08-16 ROwen    Document statusBar parameter
2012-11-14 ROwen    Stop using Checkbutton indicatoron=False; it is no longer supported on MacOS X.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import RO.TkUtil
import RO.StringUtil
import TUI.Models
import opscore.actor.keyvar
import TUI.Base.Wdg
import LimitParser

class CollWdgSet(object):
    _CollCat = "coll"
    def __init__(self, gridder, statusBar, colSpan=3, helpURL=None):
        """Create a CollWdgSet
        
        Inputs:
        - gridder: an instance of RO.Wdg.Gridder;
            the widgets are gridded starting at the next row and default column
        - statusBar: status bar (to send commands)
        - colSpan: the number of columns to span
        - helpURL: path to an HTML help file or None
        
        Note: you may wish to call master.columnconfigure(n, weight=1)
        where n is the last column of this widget set
        so that the environment widget panel can fill available space
        without resizing the columns of other widgets.
        """
        self.helpURL = helpURL
        
        self.gridder = gridder
        master = self.gridder._master
        
        self.model = TUI.Models.getModel("apogee")

        self.showHideWdg = RO.Wdg.Checkbutton(
            master = master,
            text = "Collimator",
            callFunc = self._doShowHide,
            helpText = "Show collimator controls?",
            helpURL = helpURL,
        )
        
        self.summaryWdg = RO.Wdg.StrLabel(
            master = master,
            anchor = "w",
            helpText = "Collimator status",
            helpURL = helpURL,
        )
        gridder.gridWdg(self.showHideWdg, self.summaryWdg, sticky="w", colSpan=colSpan-1)
        
        # hidable frame showing the controls

        self.detailWdg = Tkinter.Frame(
            master = master,
            borderwidth = 1,
            relief = "solid",
        )
        self.gridder.gridWdg(False, self.detailWdg, colSpan=colSpan, sticky="w", cat=self._CollCat)
        
        row = 0

        self.pistonWdg = CollItemWdg(
            master = self.detailWdg,
            name = "Piston",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        self.pistonWdg.grid(row=row, column=0, columnspan=4, sticky="w")
        row += 1

        self.pitchWdg = CollItemWdg(
            master = self.detailWdg,
            name = "Pitch",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        self.pitchWdg.grid(row=row, column=0, columnspan=4, sticky="w")
        row += 1

        self.yawWdg = CollItemWdg(
            master = self.detailWdg,
            name = "Yaw",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        self.yawWdg.grid(row=row, column=0, columnspan=4, sticky="w")
        row += 1
        
        self.model = TUI.Models.getModel("apogee")
        self.model.collOrient.addCallback(self._collOrientCallback)
        self.model.collIndexer.addCallback(self._updSummary)
        self.model.collLimitSwitch.addCallback(self._updSummary)

        self.showHideWdg.addCallback(self._doShowHide, callNow = True)
        
    def _collOrientCallback(self, keyVar):
        """collOrient keyword callback
        """
        self.pistonWdg.currFocusWdg.set(keyVar[0], isCurrent=keyVar.isCurrent)
        self.pitchWdg.currFocusWdg.set(keyVar[1], isCurrent=keyVar.isCurrent)
        self.yawWdg.currFocusWdg.set(keyVar[2], isCurrent=keyVar.isCurrent)

    def _doShowHide(self, wdg=None):
        argDict = {
            self._CollCat: self.showHideWdg.getBool(),
        }
        self.gridder.showHideWdg(**argDict)
    
    def _updSummary(self, *dumArgs):
        """Update collimator summary label
        """
        severity = RO.Constants.sevNormal
        sumStr = "OK"
        isCurrent = self.model.collIndexer.isCurrent
        
        if self.model.collIndexer[0] == False:
            sumStr = "Off"
            severity = RO.Constants.sevError
        else:
            limStrList, severity = LimitParser.limitParser(self.model.collLimitSwitch)
            if severity != RO.Constants.sevNormal:
                sumStr = "Limits %s" % (" ".join(limStrList))
        
        self.summaryWdg.set(sumStr, isCurrent=isCurrent, severity=severity)


class CollItemWdg(TUI.Base.Wdg.FocusWdg):
    """Control piston, pitch or yaw
    """
    def __init__(self, master, name, statusBar, helpURL=None):
        self.actor = "apogee"
        self.cmdVerb = name.lower()
        if self.cmdVerb == "piston":
            increments = (10, 25, 50, 100)
            defIncr = increments[1]
            units = RO.StringUtil.MuStr + "m"
            formatStr = "%0.0f"
        else:
            increments = "0.1 0.25 0.5 0.75 1 2".split()
            defIncr = increments[3]
            units = "pix"
            formatStr = "%0.2f"

        TUI.Base.Wdg.FocusWdg.__init__(self,
            master,
            label = name,
            statusBar = statusBar,
            increments = increments,
            defIncr = defIncr,
            helpURL = helpURL,
            formatStr = formatStr,
            focusWidth = 8,
            units = units,
            buttonFrame = None,
        )
        self.labelWdg["width"] = 5
        self.unitsWdg["width"] = 3
        self.setButton.grid_remove()
    
    def createFocusCmd(self, newFocus, isIncr=False):
        """Create and return the focus command. Called by the base class.
        """
        if not isIncr:
            raise RuntimeError("Absolute moves are not supported")
        cmdStr = "coll %s=%s" % (self.cmdVerb, newFocus)

        return opscore.actor.keyvar.CmdVar (
            actor = self.actor,
            cmdStr = cmdStr,
        )


if __name__ == "__main__":
    import TestData
    import TUI.Base.Wdg
    
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot

    statusBar = TUI.Base.Wdg.StatusBar(root)

    testFrame = Tkinter.Frame(root)
    gridder = RO.Wdg.Gridder(testFrame)
    collWdgSet = CollWdgSet(gridder, statusBar)
    testFrame.pack(side="top", expand=True)
    testFrame.columnconfigure(2, weight=1)

    statusBar.pack(side="top", expand=True, fill="x")

    TestData.start()

    tuiModel.reactor.run()
