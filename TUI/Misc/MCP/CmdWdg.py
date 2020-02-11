#!/usr/bin/env python
"""Controls for the MCP

History:
2011-09-02 ROwen
2013-09-05 ROwen    Added Enable Commands checkbutton for ticket #1745
2015-03-18 ROwen    Changed cancel button text from "X" to " X " for better appearance on MacOS.
                    Removed an unused variable.
2015-04-02 ROwen    Changed " X " back to "X", since I put a better solution in RO.
"""
import tkinter
import RO.Constants
import RO.Wdg
import TUI.Models
from . import BipolarDeviceWdg

class CmdWdg (tkinter.Frame):
    def __init__(self,
        master,
        statusBar,
        helpURL = None,
    **kargs):
        """Create a widget to control the MCP
        """
        tkinter.Frame.__init__(self, master, **kargs)
        self.statusBar = statusBar
        
        self.mcpModel = TUI.Models.getModel("mcp")
        self.gridder = RO.Wdg.Gridder(self, sticky="w")
        self.devList = []
        
        iackDev = BipolarDeviceWdg.IackDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            helpURL = helpURL,
        )
        self.addDev(iackDev)
        
        petalsDev = BipolarDeviceWdg.PetalsDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            helpURL = helpURL,
        )
        self.addDev(petalsDev)
        
        ffLampDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ffl",
            cmdKeyVar = self.mcpModel.ffLampCommandedOn,
            measKeyVar = self.mcpModel.ffLamp,
            helpURL = helpURL,
        )
        self.addDev(ffLampDev)
        
        hgCdDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "hgcd",
            cmdKeyVar = self.mcpModel.hgCdLampCommandedOn,
            measKeyVar = self.mcpModel.hgCdLamp,
            helpURL = helpURL,
        )
        self.addDev(hgCdDev)

        neDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ne",
            cmdKeyVar = self.mcpModel.neLampCommandedOn,
            measKeyVar = self.mcpModel.neLamp,
            helpURL = helpURL,
        )
        self.addDev(neDev)

        uvDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "uv",
            cmdKeyVar = self.mcpModel.uvLampCommandedOn,
            measKeyVar = None,
            helpURL = helpURL,
        )
        self.addDev(uvDev)

        whtDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "wht",
            cmdKeyVar = self.mcpModel.whtLampCommandedOn,
            measKeyVar = None,
            helpURL = helpURL,
        )
        self.addDev(whtDev)
        
        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "X",
            callFunc = self._doCancel,
            helpText = "Cancel all pending commands",
            helpURL = helpURL,
        )
        
        self.enableCmdsBtn = RO.Wdg.Checkbutton(
            master = self,
            text = "Enable Commands?",
            defValue = True,
            callFunc = self._doEnableCmds,
            helpText = "enable commands?",
            helpURL = helpURL,
        )
        
        self.gridder.gridWdg(False, (self.enableCmdsBtn, self.cancelBtn))
        
        self.enableButtons()
    
    def addDev(self, dev):
        self.devList.append(dev)
        self.gridder.gridWdg(dev.name, dev.cmdBtn, dev.stateWdg, sticky=None)
        
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

    def _doCancel(self, wdg=None):
        """Cancel all pending commands"""
        for dev in self.devList:
            dev.cancelCmd()
    
    def _doEnableCmds(self, wdg=None):
        """Set readOnly state of command widgets
        """
        readOnly = not self.enableCmdsBtn.getBool()
        for dev in self.devList:
            dev.setReadOnly(readOnly)

    def __str__(self):
        return self.__class__.__name__

        
if __name__ == '__main__':
    from . import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    testFrame = CmdWdg(root)
    testFrame.pack()

    tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()
