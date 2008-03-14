#!/usr/bin/env python
"""Status for Dual Imaging Spectrograph.

To Do:
- make window wide enough that changing the turret position doesn't change the window width
- make choice of turret not change spacing of x,y or blue/red items
- add a display to ccd window that shows the current size of the window
  (this will be easier once the widget container stuff is in place)  

History:
2003-03-10 ROwen    Preliminary attempt. Lots to do.
2003-03-11 ROwen    Added mask, filter and turret menus (after overhauling RO.Wdg.OptionMenu)
2003-03-14 ROwen    Added command list retrieval; wired up the lambda widgets correctly.
2003-03-17 ROwen    Improved layout and units labelling; mod. for new keywords.
2003-03-24 ROwen    Modified to use Model.getModel().
2003-30-27 ROwen    Renamed Configure button to Apply.
2003-04-03 ROwen    If command cannot be formatted, print msg to statusBar;
                    improved cancel and clear logic.
2003-04-14 ROwen    New try with ! instead of checkboxes.
2003-04-21 ROwen    Renamed StatusWdg to StatusBar to avoid conflicts.
2008-02-11 ROwen    Modified to use new TUI.Inst.StatusConfigWdg.
2008-02-12 ROwen    Modified to use InstName for the Expose window.
2008-03-13 ROwen    Simplified the test code (copying that for NICFPS).
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
    root.resizable(width=0, height=0)
    
    import TestData
    tlSet = TestData.tuiModel.tlSet

    addWindow(tlSet)
    tlSet.makeVisible("Inst.%s" % (InstName,))
    
    TestData.dispatch()
    
    root.mainloop()
