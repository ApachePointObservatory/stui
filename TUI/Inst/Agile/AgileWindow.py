#!/usr/bin/env python
"""Status/config and exposure windows for Agile.

History:
2008-10-24 ROwen
2009-01-28 ROwen    Put all Agile controls in one window.
                    Added gain, read rate and extSync controls.
2009-02-05 ROwen    Bug fix: amplifier gain option medium corrected to med.
2009-02-25 ROwen    Added display of camera connection state.
                    Modified getExpCmdStr to raise an exception if the camera is not connected.
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import TUI.Inst.StatusConfigWdg
import StatusConfigInputWdg
import AgileModel

InstName = StatusConfigInputWdg.StatusConfigInputWdg.InstName

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "Inst.%s" % (InstName,),
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = AgileExposeWindow,
        visible = False,
    )

class AgileExposeWindow(TUI.Inst.ExposeWdg.ExposeWdg):
    HelpPrefix = 'Instruments/%sWin.html#' % (InstName,)
    def __init__(self, master):
        TUI.Inst.ExposeWdg.ExposeWdg.__init__(self, master, instName=InstName)
        gr = self.expInputWdg.gridder
        
        self.gainWdg = RO.Wdg.OptionMenu(
            master = self.expInputWdg,
            items = ("Low", "Med", "High"),
            defValue = "Med",
            defMenu = "Default",
            helpText = "CCD amplifier gain",
            helpURL = self.HelpPrefix + "Gain",
        )
        gr.gridWdg("Gain", self.gainWdg, colSpan=2)
        
        self.readRateWdg = RO.Wdg.OptionMenu(
            master = self.expInputWdg,
            items = ("Slow", "Fast"),
            defValue = "Fast",
            defMenu = "Default",
            helpText = "CCD readout rate",
            helpURL = self.HelpPrefix + "ReadRate",
        )
        gr.gridWdg("Read Rate", self.readRateWdg, colSpan=2)
        
        self.statusConfigWdg = StatusConfigInputWdg.StatusConfigInputWdg(
            master = self.expInputWdg,
        )
        gr.gridWdg(False, self.statusConfigWdg, colSpan=10, sticky="w")
        self.configWdg.pack_forget()
        
        self.connSensitiveWdgSet = (self.startWdg, self.stopWdg, self.abortWdg)
        self.agileModel = AgileModel.getModel()

    def getExpCmdStr(self):
        """Get exposure command string"""
        connState, isCurrent = self.agileModel.cameraConnState.getInd(0)
        if connState and connState.lower() != "connected":
            raise RuntimeError("Wait for camera to be connected")
        cmdStr = self.expInputWdg.getString()
        if cmdStr == None:
            return
        cmdStr += " gain=%s readrate=%s" % (self.gainWdg.getString().lower(), self.readRateWdg.getString().lower())
        return cmdStr
        

if __name__ == "__main__":
    import RO.Wdg

    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)
    
    import TestData
    tlSet = TestData.tuiModel.tlSet

    addWindow(tlSet)
    tlSet.makeVisible("Inst.%s" % (InstName,))
    
    TestData.dispatch()
    
    root.mainloop()
