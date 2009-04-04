#!/usr/bin/env python
"""Status and control for the MCP

History:
2009-04-03 ROwen
"""
import Tkinter
import RO.Constants
import RO.Wdg
import opscore.actor.keyvar
import TUI.Base.Wdg
import MCPModel

_HelpURL = "Misc/MCPWin.html"

class Device(object):
    """Represents a device with a bipolar commanded state and a possibly more complex measured state"""
    def __init__(self,
        master,
        name,
        model,
        doCmdFunc,
        btnStrs,
        cmdStrs,
        cmdKeyVar,
        measKeyVar=None,
        devNames=(),
        stateNameDict = None,
        stateCharDict = None,
        btnMeasStateDict = None,
        warnStates = (),
        errorStates = (),
    ):
        """Create a Device
        
        Inputs:
        - master: parent widget
        - model: model for this actor
        - doCmdFunc: function that runs a command, taking one cmdVar as argument
        - name: name of device, for help string
        - btnStrs: a pair of strings for the button: in order False/True
        - cmdStrs: a pair of command strings: in order: command button False/True
        - cmdKeyVar: the keyVar for the commanded state
        - measKeyVar: the keyVar for the measured state, if any
        - devNames: name of each device in measKeyVar
        - stateNameDict: dict of meas state: name to report it by
        - stateCharDict: dict of meas report state name: summary char
        - btnMeasStateDict: dict of bool cmd button state: corresponding meas report state name
        - warnStates: report state names that produce a warning
        - errorStates: reported state names that indicate an error
        """
        self.master = master
        self.name = name
        self.model = model
        self.doCmdFunc = doCmdFunc
        if len(btnStrs) != 2:
            raise ValueError("btnStrs=%s must have 2 elements" % (btnStrs,))
        if len(cmdStrs) != 2:
            raise ValueError("cmdStrs=%s must have 2 elements" % (cmdStrs,))
        self.btnStrs = btnStrs
        self.cmdStrs = cmdStrs
        self.cmdKeyVar = cmdKeyVar
        self.measKeyVar = measKeyVar
        self.devNames = devNames
        self.stateNameDict = stateNameDict or dict()
        self.stateCharDict = stateCharDict or dict()
        self.btnMeasStateDict = btnMeasStateDict or dict()
        self.warnStates = warnStates        
        self.errorStates = errorStates
        self.cmdBtn = RO.Wdg.Checkbutton(
            master = self.master,
            callFunc = self.cmdBtnCallback,
            indicatoron = False,
            helpText = "Commanded state of %s" % (self.name,),
            helpURL = _HelpURL,
        )
        self.stateNameDict = stateNameDict or dict()
        self.stateCharDict = stateCharDict or dict()
        self.btnMeasStateDict = btnMeasStateDict or dict()
        if self.measKeyVar:
            self.stateWdg = RO.Wdg.StrLabel(
                master = self.master,
                anchor = "w",
                formatFunc = unicode,
                width = 15,
                helpText = "Measured state of %s" % (self.name,),
                helpURL = _HelpURL,
            )
        else:
            self.stateWdg = None
        self.tuiModel = TUI.TUIModel.Model()
            
        self.enableCmds = True
        self.pendingCmd = None

        if self.measKeyVar:
            self.measKeyVar.addCallback(self.stateCallback, callNow=False)
        self.cmdKeyVar.addCallback(self.stateCallback, callNow=True)
        self.enableBtn()
    
    def cancelCmd(self, *args):
        if self.hasPendingCmd:
            self.pendingCmd.abort()

    def enableBtn(self, *args):
        self.cmdBtn.setEnable(not self.hasPendingCmd)
        if self.hasPendingCmd:
            return
        self.enableCmds = False
        try:
            cmdState = self.getCmdState()
            btnStr = self.btnStrs[int(cmdState)]
            self.cmdBtn["text"] = btnStr
            self.cmdBtn.setBool(cmdState)
        finally:
            self.enableCmds = True
        self.updateMeasState()
    
    def getCmdState(self):
        rawState = self.cmdKeyVar[0]
        if rawState == None:
            return False
        return bool(rawState)
    
    @property
    def hasPendingCmd(self):
        return bool(self.pendingCmd and not self.pendingCmd.isDone)

    def cmdBtnCallback(self, wdg=None):
        """Command button callback"""
        if not self.enableCmds:
            return
        cmdState = self.cmdBtn.getBool()
        cmdStr = self.cmdStrs[int(cmdState)]
        if cmdStr != None:
            cmdVar = opscore.actor.keyvar.CmdVar(
                actor = self.model.actor,
                cmdStr = cmdStr,
                callFunc = self.enableBtn,
            )
            self.pendingCmd = cmdVar
            self.doCmdFunc(cmdVar)
        
        # set button state; schedule this to avoid a display bug of the change not sticking
        self.tuiModel.reactor.callLater(0.01, self.setCmdBtn, cmdState)
    
    def setCmdBtn(self, desState):
        """Set command button to desired logical state.
        """
        btnStr = self.btnStrs[int(desState)]
        self.enableCmds=False
        try:
            self.cmdBtn.setBool(desState)
            self.cmdBtn["text"] = btnStr
            self.enableBtn()
            self.cmdBtn.setEnable(not self.hasPendingCmd)
        finally:
            self.enableCmds=True
        self.updateMeasState()

    def updateMeasState(self):
        """Update measured state, but do not affect buttons"""
        if not self.measKeyVar:
            return
        isCurrent = self.measKeyVar.isCurrent

        stateStr, severity = self.formatStateStr()
        if not isCurrent:
            severity = RO.Constants.sevNormal
        self.stateWdg.set(stateStr, severity=severity, isCurrent=isCurrent)
    
    def stateCallback(self, *args):
        """Update flat-field leaf status"""
        self.updateMeasState()
        self.enableBtn()

    def formatStateStr(self):
        """Format a state string for a set of devices
        
        Return a formatted string and a severity
        """
        measStates = self.measKeyVar.valueList
#        print "measStates = %s = %s" % (measStates, [str(state) for state in measStates])

        if len(self.devNames) != len(measStates):
            raise RuntimeError("devNames=%s, measStates=%s; lengths do not match" % (self.devNames, measStates))
        
        devStateByName = [self.stateNameDict.get(state, str(state)) for state in measStates]
#        print "devStateByName=", devStateByName
        
        numDevs = len(self.devNames)
        # order the severities so we can keep track of maximum severity encountered
        sevIndexDict = {
            0: RO.Constants.sevNormal,
            1: RO.Constants.sevWarning,
            2: RO.Constants.sevError,
        }
        # a dictionary of non-normal severity states: state: index, but omitting normal
        sevStateIndexDict = dict()
        for state in self.warnStates:
            sevStateIndexDict[state] = 1
        for state in self.errorStates:
            sevStateIndexDict[state] = 2

        # a dictionary of state name: list of indices (as strings) of devices in this list
        defStateByChar = [self.stateCharDict.get(stateName, stateName) for stateName in devStateByName]
#        print "defStateByChar =", defStateByChar
        stateDict = {}
        for devName, devState in zip(self.devNames, devStateByName):
            devList = stateDict.setdefault(devState, [])
            devList.append(str(devName)) # use str in case devName is an integer

        sevIndex = 0
        cmdBtnState = self.cmdBtn.getBool()
        desMeasState = self.btnMeasStateDict.get(cmdBtnState, None)
        for state, devList in stateDict.iteritems():
            sevIndex = max(sevIndex, sevStateIndexDict.get(state, 0))
            if desMeasState and state not in ("None", desMeasState):
                sevIndex = max(sevIndex, 1)
            if len(devList) == numDevs:
                stateStr = "All " + str(state)
                return stateStr, sevIndexDict[sevIndex]
            stateChar = self.stateCharDict.get(state, "?")
        if desMeasState:
            sevIndex = max(sevIndex, 1)
        return " ".join(defStateByChar), sevIndexDict[sevIndex]
    
        def __str__(self):
            return self.__class__.__name__

class IackDevice(Device):
    def __init__(self, master, model, doCmdFunc):
        Device.__init__(self,
            master = master,
            name = "Iack",
            model = model,
            doCmdFunc = doCmdFunc,
            btnStrs = ("Needed", "Done"),
            cmdStrs = (None, "iack"),
            cmdKeyVar = model.needIack,
            measKeyVar = None,
        )

    def enableBtn(self, *args):
        """Once this button is pushed, leave it pushed (unless the device un-iacks)"""
        Device.enableBtn(self)
        if self.cmdBtn.getBool():
            self.cmdBtn.setEnable(False)
    
    def getCmdState(self):
        """Override because cmdKeyVar is inverted from the norm"""
        rawState = self.cmdKeyVar[0]
        if rawState == None:
            return False
        return bool(not rawState)

class PetalsDevice(Device):
    def __init__(self, master, model, doCmdFunc):
        stateNameDict = {
            "None": "?",
            "00": "?",
            "01": "Closed",
            "10": "Open",
            "11": "Invalid",
        }
        stateCharDict = {
            "?": "?",
            "Closed": "-",
            "Open": "|",
            "Invalid": "X",
        }
        btnMeasStateDict = {
            False: "Closed",
            True: "Open",
        }
        Device.__init__(self,
            master = master,
            name = "FF Petals",
            model = model,
            doCmdFunc = doCmdFunc,
            btnStrs = ("Closed", "Opened"),
            cmdStrs = ("ffs_close", "ffs_open"),
            cmdKeyVar = model.ffsCommandedOn,
            measKeyVar = model.ffsStatus,
            devNames = [str(ind+1) for ind in range(8)],
            stateNameDict = stateNameDict,
            stateCharDict = stateCharDict,
            btnMeasStateDict = btnMeasStateDict,
            warnStates = ("?",),
            errorStates = ("Invalid",),
        )

class LampDevice(Device):
    def __init__(self, master, name, model, doCmdFunc, cmdKeyVar, measKeyVar=None):
        stateNameDict = {
            "None": "?",
            False: "Off",
            True: "On",
        }
        stateCharDict = {
            "?": "?",
            "Off": u"\N{BULLET}",
            "On": u"\N{EIGHT POINTED BLACK STAR}",
        }
        btnMeasStateDict = {
            False: "Off",
            True: "On",
        }
        lowName = name.lower()
        cmdStrs = ["%s_%s" % (name.lower(), cmd) for cmd in ("off", "on")]
        Device.__init__(self,
            master = master,
            name = name,
            model = model,
            doCmdFunc = doCmdFunc,
            btnStrs = ("Off", "On"),
            cmdStrs = cmdStrs,
            cmdKeyVar = cmdKeyVar,
            measKeyVar = measKeyVar,
            devNames = [str(ind+1) for ind in range(4)],
            stateNameDict = stateNameDict,
            stateCharDict = stateCharDict,
            btnMeasStateDict = btnMeasStateDict,
        )
        self.cmdBtn.helpText += " lamps"
        if self.stateWdg:
            self.stateWdg.helpText += " lamps"


class MCPWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a widget to control the MCP
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.mcpModel = MCPModel.Model()
        
        gr = RO.Wdg.Gridder(self, sticky="e")
        self.gridder = gr
        self.devList = []
        
        iackDev = IackDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
        )
        self.addDev(iackDev)
        
        petalsDev = PetalsDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
        )
        self.addDev(petalsDev)
        
        ffLampDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ffl",
            cmdKeyVar = self.mcpModel.ffLampCommandedOn,
            measKeyVar = self.mcpModel.ffLamp,
        )
        self.addDev(ffLampDev)
        
        hgCdDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "hgcd",
            cmdKeyVar = self.mcpModel.hgCdLampCommandedOn,
            measKeyVar = self.mcpModel.hgCdLamp,
        )
        self.addDev(hgCdDev)

        neDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ne",
            cmdKeyVar = self.mcpModel.neLampCommandedOn,
            measKeyVar = self.mcpModel.neLamp,
        )
        self.addDev(neDev)

        uvDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "uv",
            cmdKeyVar = self.mcpModel.uvLampCommandedOn,
            measKeyVar = None,
        )
        self.addDev(uvDev)

        whtDev = LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "wht",
            cmdKeyVar = self.mcpModel.whtLampCommandedOn,
            measKeyVar = None,
        )
        self.addDev(whtDev)

        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "Cancel",
            callFunc = self._cancelBtnCallback,
            helpText = "Cancel all pending commands",
            helpURL = _HelpURL,
        )
        gr.gridWdg(self.cancelBtn)
        
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = _HelpURL,
        )

        gr.gridWdg(False, self.statusBar, colSpan=10, sticky="ew")
        
        self.enableButtons()
    
    def addDev(self, dev):
        self.devList.append(dev)
        self.gridder.gridWdg(dev.name, dev.cmdBtn, dev.stateWdg, sticky=None)

    def _cancelBtnCallback(self, wdg=None):
        """Cancel all pending commands"""
        for dev in self.devList:
            dev.cancelCmd()
        
    def doCmd(self, cmdVar):
        """Execute a command variable and update cancel button state"""
        cmdVar.addCallback(self.enableCancelBtn)
        self.statusBar.doCmd(cmdVar)
        self.enableCancelBtn()
    
    def enableCancelBtn(self, *args):
        hasPendingCmds = False
        for dev in self.devList:
            hasPendingCmds |= dev.hasPendingCmd
        self.cancelBtn.setEnable(hasPendingCmds)
        
    def enableButtons(self, *args):
        """Enable or disable buttons"""
        self.enableCancelBtn()
        for dev in self.devList:
            dev.enableBtn()

    def __str__(self):
        return self.__class__.__name__

        
if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = MCPWdg(root)
    testFrame.pack()

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.init()

    tuiModel.reactor.run()
