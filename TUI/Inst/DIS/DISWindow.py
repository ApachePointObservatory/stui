#!/usr/local/bin/python
from __future__ import generators
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
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import StatusConfigWdg

def addWindow(tlSet):
    tlSet.createToplevel (
        name = "None.DIS Expose",
        defGeom = "+452+280",
        resizable = False,
        wdgFunc = RO.Alg.GenericCallback (
            TUI.Inst.ExposeWdg.ExposeWdg,
            instName = "DIS",
        ),
        visible = False,
    )
    
    tlSet.createToplevel (
        name = "Inst.DIS",
        defGeom = "+676+280",
        resizable = False,
        wdgFunc = StatusConfigWdg.StatusConfigWdg,
        visible = False,
    )


if __name__ == "__main__":
    import RO.Wdg

    root = RO.Wdg.PythonTk()
    
    import TestData

    addWindow(TestData.tuiModel.tlSet)
    expTl = TestData.tuiModel.tlSet.getToplevel("None.DIS Expose")
    expFrame = expTl.getWdg()
    mainTl = TestData.tuiModel.tlSet.getToplevel("Inst.DIS")
    mainTl.makeVisible()
    mainFrame = mainTl.getWdg()

    TestData.dispatch()
    
    root.mainloop()
