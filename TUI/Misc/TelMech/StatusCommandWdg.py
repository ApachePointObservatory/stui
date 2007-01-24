#!/usr/bin/env python
from __future__ import generators
"""Status and control for the enclosure controller.

To do:
- CRUCIAL: update test data code
- Add "All On"/"All Off" buttons for heaters and louvers.
- Add Exhaust button for fans?
- Add "Dome Off" for lights that turns off lights that interfere with observing?
- Highlight states which do not permit observing (e.g. enclosure lights on) in warning color

History:
2005-08-02 ROwen
2005-08-15 ROwen    Modified to not show enclosure enable (it doesn't seem to do anything).
2005-10-13 ROwen    Removed unused globals.
2006-05-04 ROwen    Modified to use telmech actor instead of tcc (in process!!!)
"""
import Tkinter
import RO.Alg
import RO.Constants
import RO.Wdg
import TUI.TUIModel
import TelMechModel

_HelpURL = "Misc/EnclosureWin.html"

_ColsPerDev = 3 # number of columns for each device widget

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
        # wdgDict keys are category names
        # values are a list of (label wdg, ctrl wdg, readOnly), one per device
#       self.wdgDict = RO.Alg.ListDict()
        
        self._updating = False

        self.row = 0
        self.col = 0
        
#       self.addCategory("Enable")
#       self.row += 1
        self.addCategory("Shutters")
#       self.row += 1
        self.addCategory("Fans")
        self.addCategory("Lights", newCol=True)
        self.addCategory("Louvers", newCol=True)
        self.addCategory("Heaters", newCol=True)
    
    def addCategory(self, catName, newCol=False):
        """Add a set of widgets for a category of devices"""
        if newCol:
            self.row = 0
            self.col += _ColsPerDev
            RO.Wdg.StrLabel(self, text=" ").grid(row=self.row, column=self.col)
            self.col += 1
        
        catInfo = self.model.catDict[catName]

        self.addCategoryLabel(catName)
        self.addDevWdgs(catInfo)
        
    def addCategoryLabel(self, catName):
        """Add a label for a category of devices"""
        labelWdg = RO.Wdg.StrLabel(self, text=catName)
        labelWdg.grid(
            row = self.row,
            column = self.col,
            columnspan = _ColsPerDev,
        )
        self.row += 1
    
    def addDevWdgs(self, catInfo):
        """Add a set of widgets to control one device.
        Returns those widgets.
        """
#       print "addDevWdgs(catInfo=%r, devName=%r)" % (catInfo, devName)
        stateWidth = max([len(name) for name in catInfo.stateNames])

        for devName, keyVar in catInfo.devDict.iteritems():
            labelWdg = RO.Wdg.StrLabel(
                master = self,
                text = devName,
                anchor = "e",
                helpText = None,
                helpURL = _HelpURL,
            )
            
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

#           self.wdgDict[catInfo.catName] = (labelWdg, ctrlWdg, catInfo.readOnly)
    
    def cmdFailed(self, wdg, *args, **kargs):
        """A command failed. Redraw the appropriate button
        (for simplicity, redraw the entire category).
        Use after because a simple callback will not have the right effect
        if the command fails early during the command button callback.
        """
        self.after(10, wdg.restoreDefault)
    
    def _doCmd(self, catInfo, devName, ctrlWdg):
#       print "_doCmd(catInfo=%r, devName=%r, ctrlWdg=%r)" % (catInfo, devName, ctrlWdg)
        print "_doCmd(%s)" % devName
        if self._updating:
            # updating status rather than executing a command
            return

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

#   Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
#   TestData.dispatch()
    
    root.mainloop()
