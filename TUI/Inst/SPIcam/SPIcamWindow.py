#!/usr/bin/env python
"""Status and configuration for SPIcam.

History:
2007-05-22 ROwen
2008-02-11 ROwen    Modified to use new TUI.Inst.StatusConfigWdg.
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import TUI.Inst.StatusConfigWdg
import StatusConfigInputWdg

InstName = StatusConfigInputWdg.StatusConfigInputWdg.InstName

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "None.%s Expose" % (InstName,),
        defGeom = "+452+280",
        resizable = False,
        wdgFunc = RO.Alg.GenericCallback (
            TUI.Inst.ExposeWdg.ExposeWdg,
            instName = "DIS",
        ),
        visible = False,
    )
    
    tlSet.createToplevel (
        name = "Inst.%s" % (InstName,),
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = StatusConfigWdg,
        visible = False,
    )

class StatusConfigWdg(TUI.Inst.StatusConfigWdg.StatusConfigWdg):
    def __init__(self, master):
        TUI.Inst.StatusConfigWdg.StatusConfigWdg.__init__(self,
            master = master,
            statusConfigInputClass = StatusConfigInputWdg.StatusConfigInputWdg,
        )


if __name__ == "__main__":
    import RO.Wdg

    root = RO.Wdg.PythonTk()
    
    import TestData

    addWindow(TestData.tuiModel.tlSet)
    expTl = TestData.tuiModel.tlSet.getToplevel("None.SPIcam Expose")
    expFrame = expTl.getWdg()
    mainTl = TestData.tuiModel.tlSet.getToplevel("Inst.SPIcam")
    mainTl.makeVisible()
    mainFrame = mainTl.getWdg()

    TestData.dispatch()
    
    root.mainloop()
