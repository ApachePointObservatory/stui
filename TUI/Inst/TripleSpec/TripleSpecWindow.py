#!/usr/bin/env python
"""Status/config and exposure windows for the Echelle.

History:
2008-03-14 ROwen
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
            instName = InstName,
        ),
        visible=False,
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
            actor = "tspec",
        )

    def getActorForCommand(self, cmdStr):
        cmdWords = cmdStr.split(None, 1)
        if len(cmdWords) < 1:
            return "tspec"
        cmdVerb = cmdWords[0].lower()
        if "slit" in cmdVerb:
            return "tcamera"
        else:
            return "tspec"

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
