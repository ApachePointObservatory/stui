#!/usr/bin/env python
"""Status and control for the MCP

History:
2009-04-03 ROwen
2009-07-09 ROwen    Modified button enable code.
2009-08-25 ROwen    Modified for change to mcp dictionary: ffsCommandedOn -> ffsCommandedOpen.
2010-03-12 ROwen    Changed to use Models.getModel.
2010-06-28 ROwen    Bug fix: Device.__str__ was not defined due to incorrect indentation (thanks to pychecker).
                    Removed two statements that had no effect (thanks to pychecker).
2010-10-29 ROwen    Added counterweight status and spectrograph slithead status.
                    Moved bipolar device code to a new module BipolarDeviceWdg.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import opscore.actor.keyvar
import TUI.Base.Wdg
import TUI.Models
import BipolarDeviceWdg
import CounterweightWdg
import SlitheadWdg

_HelpURL = "Misc/MCPWin.html"

class MCPWdg (Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        """Create a widget to control the MCP
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        self.mcpModel = TUI.Models.getModel("mcp")
        
        gr = RO.Wdg.Gridder(self, sticky="e")
        self.gridder = gr
        self.devList = []
        
        iackDev = BipolarDeviceWdg.IackDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            helpURL = _HelpURL,
        )
        self.addDev(iackDev)
        
        petalsDev = BipolarDeviceWdg.PetalsDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            helpURL = _HelpURL,
        )
        self.addDev(petalsDev)
        
        ffLampDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ffl",
            cmdKeyVar = self.mcpModel.ffLampCommandedOn,
            measKeyVar = self.mcpModel.ffLamp,
            helpURL = _HelpURL,
        )
        self.addDev(ffLampDev)
        
        hgCdDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "hgcd",
            cmdKeyVar = self.mcpModel.hgCdLampCommandedOn,
            measKeyVar = self.mcpModel.hgCdLamp,
            helpURL = _HelpURL,
        )
        self.addDev(hgCdDev)

        neDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "ne",
            cmdKeyVar = self.mcpModel.neLampCommandedOn,
            measKeyVar = self.mcpModel.neLamp,
            helpURL = _HelpURL,
        )
        self.addDev(neDev)

        uvDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "uv",
            cmdKeyVar = self.mcpModel.uvLampCommandedOn,
            measKeyVar = None,
            helpURL = _HelpURL,
        )
        self.addDev(uvDev)

        whtDev = BipolarDeviceWdg.LampDevice(
            master = self,
            model = self.mcpModel,
            doCmdFunc = self.doCmd,
            name = "wht",
            cmdKeyVar = self.mcpModel.whtLampCommandedOn,
            measKeyVar = None,
            helpURL = _HelpURL,
        )
        self.addDev(whtDev)
        
        nextRow = gr.getNextRow()
        gr.startNewCol(row=1)
        
        self.cwWdgList = CounterweightWdg.CounterweightWdgList(self, helpURL=_HelpURL)
        for i, wdg in enumerate(self.cwWdgList):
            gr.gridWdg("CW %d" % (i+1,), wdg)
        
        self.spSlitWdgList = SlitheadWdg.SlitheadWdgList(self, helpURL=_HelpURL)
        for i, wdg in enumerate(self.spSlitWdgList):
            gr.gridWdg("SP%d Slit" % (i+1,), wdg)

        nextRow = max(nextRow, gr.getNextRow())

        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "Cancel",
            callFunc = self._cancelBtnCallback,
            helpText = "Cancel all pending commands",
            helpURL = _HelpURL,
        )
        self.cancelBtn.grid(row=nextRow, column=0)
        nextRow += 1
        
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = _HelpURL,
        )
        self.statusBar.grid(row=nextRow, column=0, columnspan=10, sticky="ew")
        nextRow += 1
        
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
    
    TestData.start()

    tuiModel.reactor.run()
