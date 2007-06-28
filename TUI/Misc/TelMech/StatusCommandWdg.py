#!/usr/bin/env python
from __future__ import generators
"""Status and control for the enclosure controller.

To do:
- Tert Rot should track even if state is ? while rotating
  unless state is NOT ? while rotating in which case don't worry about it
- Tert Rot Apply button should gray out during rotation
  and restore itself if the command times out

History:
2005-08-02 ROwen
2005-08-15 ROwen    Modified to not show enclosure enable (it doesn't seem to do anything).
2005-10-13 ROwen    Removed unused globals.
2006-05-04 ROwen    Modified to use telmech actor instead of tcc (but not all commands supported).
2007-06-26 ROwen    Added support for Eyelid controls
                    Allow group control of lights, louvers and heaters (and hiding details)
2007-06-27 ROwen    Added support for mirror covers and tertiary rotation.
"""
import numpy
import Tkinter
import RO.Alg
import RO.Constants
import RO.Wdg
import TUI.TUIModel
import TelMechModel

_HelpURL = "Misc/EnclosureWin.html"

_ColsPerDev = 3 # number of columns for each device widget

class DevStateWdg(RO.Wdg.Label):
    """Widget that displays a summary of device state.
    
    Note: this widget registers itself with the TelMech model
    so once created it self-udpates.
    
    Inputs:
    - master: master widget
    - catInfo: category info from the TelMech model
    - onIsNormal: if True/False then severity is normal if all are on/off
    - patternDict: dict of state: (state string, severity)
        where state is a tuple of bools or ints (one per device)
    - **kargs: keyword arguments for RO.Wdg.Label
    """
    def __init__(self,
        master,
        catInfo,
        onIsNormal = True,
        patternDict = None,
    **kargs):
        kargs.setdefault("borderwidth", 2)
        kargs.setdefault("relief", "sunken")
        kargs.setdefault("anchor", "center")
        RO.Wdg.Label.__init__(self, master, **kargs)
        self.patternDict = patternDict or {}    
        self.onIsNormal = onIsNormal
        catInfo.addCallback(self.updateState)

    def updateState(self, catInfo):
        isCurrent = catInfo.devIsCurrent.all()
        stateStr, severity = self.getStateStrSev(catInfo.devState, catInfo)
        self.set(stateStr, isCurrent = isCurrent, severity = severity)

    def getStateStrSev(self, devState, catInfo):
        """Return state string associated with specified device state"""
        if numpy.isnan(devState).any():
            return ("?", RO.Constants.sevWarning)

        if self.patternDict:
            statusStrSev = self.patternDict.get(tuple(devState.astype(numpy.bool)))
            if statusStrSev != None:
                return statusStrSev
            
        if devState.all():
            if self.onIsNormal:
                severity = RO.Constants.sevNormal
            else:
                severity = RO.Constants.sevWarning
            return ("All " + catInfo.stateNames[1], severity)
        elif devState.any():
            return ("Some " + catInfo.stateNames[1], RO.Constants.sevWarning)

        # all are off
        if self.onIsNormal:
            severity = RO.Constants.sevWarning
        else:
            severity = RO.Constants.sevNormal
        return ("All " + catInfo.stateNames[0], severity)


class StatusCommandWdg (Tkinter.Frame):
    def __init__(self,
        master,
        statusBar,
    **kargs):
        """Create a new widget to show status for and configure the enclosure controller
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.statusBar = statusBar
        self.model = TelMechModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()
        
        # dict of category: sequence of detailed controls (for show/hide)
        self.detailWdgDict ={}

        self.row = 0
        self.col = 0
        
        self.addCategory("Shutters")
        self.row += 1
        self.addCategory("Fans")

        self.startNewColumn()
        RO.Wdg.StrLabel(
            master = self,
            text = "Mir Covers",
            helpURL = _HelpURL,
        ).grid(row=self.row, column=self.col)
        self.row += 1
        self.coversWdg = RO.Wdg.Checkbutton(
            master = self,
            onvalue = "Open",
            offvalue = "Closed",
            width = 6,
            autoIsCurrent = True,
            showValue = True,
            indicatoron = False,
            command = self.doCoversCmd,
            helpText = "Toggle the primary mirror covers",
            helpURL = _HelpURL,
        )
        self.model.covers.addROWdg(self.coversWdg, setDefault=True)
        self.model.covers.addROWdg(self.coversWdg)
        self.coversWdg.grid(row=self.row, column=self.col)
        self.row += 3
        
        RO.Wdg.StrLabel(
            master = self,
            text = "Tert Rot",
            helpURL = _HelpURL,
        ).grid(row=self.row, column=self.col)
        self.row += 1
        self.tertRotWdg = RO.Wdg.OptionMenu(
            master = self,
            items = self.model.catDict["Eyelids"].devDict.keys(),
            ignoreCase = True,
            width = 3,
            autoIsCurrent = True,
            helpText = "Tertiary rotation position",
            helpURL = _HelpURL,
        )
        self.tertRotWdg.grid(row=self.row, column=self.col)
        self.row += 1
        self.tertRotApplyWdg = RO.Wdg.Button(
            master = self,
            text = "Apply",
            callFunc = self.doApplyTertRot,
            helpText = "Apply tertiary rotation",
            helpURL = _HelpURL,
        )
        self.tertRotApplyWdg.grid(row=self.row, column=self.col)
        self.row += 1
        self.tertRotCurrentWdg = RO.Wdg.Button(
            master = self,
            text = "Current",
            callFunc = self.doCurrentTertRot,
            helpText = "Display current tertiary rotation",
            helpURL = _HelpURL,
        )
        self.tertRotCurrentWdg.grid(row=self.row, column=self.col)
        self.model.tertRot.addIndexedCallback(self.updateTertRot)
        self.row += 1
        
        self.startNewColumn()
        self.addCategory("Eyelids")
        
        self.startNewColumn()
        self.lightsState = DevStateWdg(
            master = self,
            catInfo = self.model.catDict["Lights"],
            onIsNormal = False,
            patternDict = {
                (0, 0, 0, 0, 0, 0, 1, 0): ("Main Off", RO.Constants.sevNormal),
            },
            helpText = "State of the lights",
            helpURL = _HelpURL,
        )
        self.lightsOffWdg = RO.Wdg.Button(
            master = self,
            text = "Main Off",
            callFunc = self.doLightsMainOff,
            helpText = "Turn off all lights except int. incandescents",
            helpURL = _HelpURL,
        )
        self.addCategory("Lights", extraWdgs=(self.lightsState, self.lightsOffWdg))
        
        self.startNewColumn()
        self.louversState = DevStateWdg(
            master = self,
            catInfo = self.model.catDict["Louvers"],
            onIsNormal = True,
            helpText = "State of the louvers",
            helpURL = _HelpURL,
        )
        self.louversOpenWdg = RO.Wdg.Button(
            master = self,
            text = "Open All",
            callFunc=self.doLouversOpen,
            helpText = "Open all louvers",
            helpURL = _HelpURL,
        )
        self.louversCloseWdg = RO.Wdg.Button(
            master = self,
            text = "Close All",
            callFunc=self.doLouversClose,
            helpText = "Close all louvers",
            helpURL = _HelpURL,
        )
        self.addCategory(
            catName = "Louvers",
            extraWdgs = (self.louversState, self.louversOpenWdg, self.louversCloseWdg),
        )
        
        self.startNewColumn()
        self.heatersState = DevStateWdg(
            master = self,
            catInfo = self.model.catDict["Heaters"],
            onIsNormal = False,
            helpText = "State of the roof heaters",
            helpURL = _HelpURL,
        )
        self.heatersOffWdg = RO.Wdg.Button(
            master = self,
            text = "All Off",
            callFunc = self.doHeatersOff,
            helpText = "Turn off all roof heaters",
            helpURL = _HelpURL,
        )
        self.heatersOnWdg = RO.Wdg.Button(
            master = self,
            text = "All On",
            callFunc=self.doHeatersOn,
            helpText = "Turn on all roof heaters",
            helpURL = _HelpURL,
        )
        self.addCategory(
            catName = "Heaters",
            extraWdgs = (self.heatersState, self.heatersOffWdg, self.heatersOnWdg),
        )
    def addCategory(self, catName, extraWdgs=None):
        """Add a set of widgets for a category of devices"""
        
        catInfo = self.model.catDict[catName]

        hasDetails = bool(extraWdgs)
        self.addCategoryLabel(catName, hasDetails)
        
        if extraWdgs:
            for ctrl in extraWdgs:
                ctrl.grid(column=self.col, row=self.row, columnspan=_ColsPerDev, sticky="ew")
                self.row += 1

        self.addDevWdgs(catInfo, doHide=extraWdgs)
        
    def addCategoryLabel(self, catName, hasDetails):
        """Add a label for a category of devices"""
        if hasDetails:
            labelWdg = RO.Wdg.Checkbutton(
                master = self,
                text = catName,
                indicatoron = False,
                callFunc = self.showHideDetails,
                helpText = "show/hide detailed info",
            )
        else:
            labelWdg = RO.Wdg.StrLabel(self, text=catName)
        labelWdg.grid(
            row = self.row,
            column = self.col,
            columnspan = _ColsPerDev,
        )
        self.row += 1
    
    def addDevWdgs(self, catInfo, doHide):
        """Add a set of widgets to control one device.
        """
#       print "addDevWdgs(catInfo=%r, devName=%r)" % (catInfo, devName)
        stateWidth = max([len(name) for name in catInfo.stateNames])
        
        wdgList = []

        for devName, keyVar in catInfo.devDict.iteritems():
            labelWdg = RO.Wdg.StrLabel(
                master = self,
                text = devName,
                anchor = "e",
                helpText = None,
                helpURL = _HelpURL,
            )
            wdgList.append(labelWdg)
            
            ctrlWdg = RO.Wdg.Checkbutton(
                master = self,
                onvalue = catInfo.stateNames[1],
                offvalue = catInfo.stateNames[0],
                width = stateWidth,
                autoIsCurrent = True,
                showValue = True,
                indicatoron = False,
                helpText = "Toggle %s %s" % (devName, catInfo.catNameSingular.lower()),
                helpURL = _HelpURL,
            )
            wdgList.append(ctrlWdg)
            ctrlWdg["disabledforeground"] = ctrlWdg["foreground"]
            if catInfo.readOnly:
                ctrlWdg.setEnable(False)
                ctrlWdg.helpText = "State of %s %s (read only)" % (devName, catInfo.catNameSingular.lower())
            else:
                ctrlWdg["command"] = RO.Alg.GenericCallback(self._doCmd, catInfo, devName, ctrlWdg)
            keyVar.addROWdg(ctrlWdg, setDefault=True)
            keyVar.addROWdg(ctrlWdg)
            
            colInd = self.col
            labelWdg.grid(row = self.row, column = colInd, sticky="e")
            colInd += 1
            ctrlWdg.grid(row = self.row, column = colInd, sticky="w")
            colInd += 1
            self.row += 1
            
            if doHide:
                labelWdg.grid_remove()
                ctrlWdg.grid_remove()

        self.detailWdgDict[catInfo.catName] = wdgList
    
    def cmdFailed(self, wdg, *args, **kargs):
        """A command failed. Redraw the appropriate button
        (for simplicity, redraw the entire category).
        Use after because a simple callback will not have the right effect
        if the command fails early during the command button callback.
        """
        self.after(10, wdg.restoreDefault)
    
    def doCoversCmd(self):
        """Open or close the primary mirror covers"""
        boolVal = self.coversWdg.getBool()
        stateStr = {True: "Closed", False: "Open"}[boolVal]
        self.coversWdg["text"] = stateStr
        verbStr = {True: "close", False: "open"}[boolVal]
        cmdStr = "covers %s" % verbStr
        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = cmdStr,
            timeLim = self.model.timeLim,
            callFunc = RO.Alg.GenericCallback(self.cmdFailed, self.coversWdg),
            callTypes = RO.KeyVariable.FailTypes,
        )
        self.statusBar.doCmd(enclCmdVar)
    
    def doApplyTertRot(self, wdg=None):
        """Apply tertiary rotation command"""
        desTertRot = self.tertRotWdg.getString().lower()
        cmdStr = "tertrot %s" % desTertRot
        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = cmdStr,
            callTypes = RO.KeyVariable.FailTypes,
        )
        self.statusBar.doCmd(enclCmdVar)  
    
    def doCurrentTertRot(self, wdg=None):
        """Restore TertRot widget to current value"""
        self.tertRotWdg.restoreDefault()
    
    def updateTertRot(self, value, isCurrent, keyVar=None):
        self.tertRotWdg.setDefault(value)
        isDefault = self.tertRotWdg.isDefault()
        self.tertRotApplyWdg.setEnable(not isDefault)
        self.tertRotCurrentWdg.setEnable(not isDefault)

    def doLightsMainOff(self, wdg=None):
        """Turn off main lights"""
        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = "lights fhalides rhalides incand platform catwalk stairs int_fluor off",
        )
        self.statusBar.doCmd(enclCmdVar)
    
    def doLouversOpen(self, wdg=None):
        """Open all louvers"""
        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = "louvers all open",
        )
        self.statusBar.doCmd(enclCmdVar)
    
    def doLouversClose(self, wdg=None):
        """Close all louvers"""
        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = "louvers all close",
        )
        self.statusBar.doCmd(enclCmdVar)
    
    def doHeatersOff(self, wdg=None):
        """Turn on all roof heaters"""
        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = "heaters all on",
        )
        self.statusBar.doCmd(enclCmdVar)

    def doHeatersOn(self, wdg=None):
        """Turn off all roof heaters"""
        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = "heaters all off",
        )
        self.statusBar.doCmd(enclCmdVar)
    
    def showHideDetails(self, wdg):
        """Show or hide detailed controls for a category"""
        catName = wdg["text"]
        doShow = wdg.getBool()
        detailWdgs = self.detailWdgDict[catName]
        if doShow:
            for wdg in detailWdgs:
                wdg.grid()
        else:
            for wdg in detailWdgs:
                wdg.grid_remove()
    
    def _doCmd(self, catInfo, devName, ctrlWdg):
#       print "_doCmd(catInfo=%r, devName=%r, ctrlWdg=%r)" % (catInfo, devName, ctrlWdg)
        print "_doCmd(%s)" % devName

        boolVal = ctrlWdg.getBool()
        stateStr = catInfo.getStateStr(boolVal)
        ctrlWdg["text"] = stateStr

        # execute the command
        verbStr = catInfo.getVerbStr(boolVal)
        cmdStr = "%s %s %s" % (catInfo.catName, devName, verbStr)
        cmdStr = cmdStr.lower()

        enclCmdVar = RO.KeyVariable.CmdVar(
            actor = self.model.actor,
            cmdStr = cmdStr,
            timeLim = self.model.timeLim,
            callFunc = RO.Alg.GenericCallback(self.cmdFailed, ctrlWdg),
            callTypes = RO.KeyVariable.FailTypes,
        )
        self.statusBar.doCmd(enclCmdVar)
    
    def startNewColumn(self):
        """Start a new column of controls"""
        self.row = 0
        self.col += _ColsPerDev
        # create narrow blank column
        RO.Wdg.StrLabel(self, text=" ").grid(row=self.row, column=self.col)
        self.col += 1

        
if __name__ == '__main__':
    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)

    import TestData
    print "import TestData"
        
    statusBar = RO.Wdg.StatusBar(root, dispatcher=TestData.dispatcher)
    testFrame = StatusCommandWdg (root, statusBar)
    testFrame.pack()
    statusBar.pack(expand="yes", fill="x")
    
    print "done building"

#    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.run()
    
    root.mainloop()
