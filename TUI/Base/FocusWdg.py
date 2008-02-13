#!/usr/bin/env python
"""General focus control.

History:
2008-02-04 ROwen
2008-02-11 ROwen    Modified to always show the cancel button (now named X instead of Cancel).
2008-02-13 ROwen    Fix PR 738: removed focus limits, since they were only a guess and getting it wrong
                    could put unreasonable limits on the user. Let the actor handle focus limits.
"""
import Tkinter
import RO.KeyVariable
import RO.Wdg
import RO.TkUtil
import RO.StringUtil
import TUI.TUIModel

MicronStr = RO.StringUtil.MuStr + "m"

class FocusWdg(Tkinter.Frame):
    def __init__ (self,
        master,
        name = None,
        statusBar = None,
        increments = None,
        defIncr = None,
        helpURL = None,
        label = "Focus",
        fmtStr = "%.1f",
        units = MicronStr,
        currLabel = "Focus",
        currWidth = 5,
        buttonFrame = None,
     **kargs):
        """A widget for displaying and specifying focus.
        
        Subclasses must override createFocusCmd and must call startTimer, endTimer and updFocus

        Inputs:
        - master        master Tk widget -- typically a frame or window
        - name          name of device whose focus is being adjusted; used for help
        - statusBar     an RO.Wdg.StatusBar widget
        - increments    focus increments (ints) for menu; defaults to 25, 50, 100
        - defIncr       default focus increment (int); defaults to increments[2]
        - fmtStr        format for displaying focus
        - units         units of focus
        - currLabel     text for current focus label
        - currWidth     width of current focus widget
        - buttonFrame   button frame; if omitted then the buttons are shown right of the current focus
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        if not increments:
            increments = (25, 50, 100)
        if not defIncr:
            defIncr = int(increments[1])

        self.name = str(name)
        self.statusBar = statusBar

        self.tuiModel = TUI.TUIModel.getModel()
        self.currCmd = None

        # current focus display
        RO.Wdg.Label(self, text=currLabel).grid(row=0, column=0)
        self.currFocusWdg = RO.Wdg.FloatLabel(
            master = self,
            formatStr = fmtStr,
            width = currWidth,
            helpText = "Current %s focus" % (self.name,),
            helpURL = helpURL,
        )
        self.currFocusWdg.grid(row=0, column=1)
        RO.Wdg.Label(self, text=units).grid(row=0, column=2)

        self.timerWdg = RO.Wdg.TimeBar(
            master = self,
            autoStop = True,
            helpText = "Estimated move time",
            helpURL = helpURL,
        )
        self.timerWdg.grid(row=0, column=3, sticky="ew")
        self.timerWdg.grid_remove()
        self.grid_columnconfigure(3, weight=1)
        
        # command buttons
        if buttonFrame == None:
            gridButtonFrame = True
            buttonFrame = Tkinter.Frame(self)
        else:
            gridButtonFrame = False
            
        col = 0
                
        self.setButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Set...",
            callFunc = self.doSet,
            helpText = "Set %s focus" % (self.name,)
        )
        self.setButton.grid(row=0, column=col)
        col += 1

        self.decreaseButton = RO.Wdg.Button(
            master=buttonFrame,
            text = "-",
            callFunc = self.doDeltaBtn,
            helpURL = helpURL,
        )
        self.decreaseButton.grid(row=0, column=col)
        col += 1

        self.increaseButton = RO.Wdg.Button(
            master=buttonFrame,
            text = "+",
            callFunc = self.doDeltaBtn,
            helpURL = helpURL,
        )
        self.increaseButton.grid(row=0, column=col)
        col += 1
        
        incrStrs = ["%s %s" % (int(incr), units) for incr in increments]
        defIncrStr = "%s %s" % (defIncr, units)
        maxIncrLength = max([len(s) for s in incrStrs])
        self.deltaMenu = RO.Wdg.OptionMenu(
            master = buttonFrame,
            items = incrStrs,
            defValue = defIncrStr,
            callFunc = self.doDeltaMenu,
            width = maxIncrLength,
            helpText = "Step size for -/+ buttons",
            helpURL = helpURL,
        )
        self.deltaMenu.grid(row=0, column=col)
        col += 1
        
        self.cancelButton = RO.Wdg.Button(
            master=buttonFrame,
            text = "X",
            callFunc = self.cmdCancel,
            helpText = "Cancel focus command",
            helpURL = helpURL,
        )
        self.cancelButton.grid(row=0, column=col)
        col += 1
        
        # allow button frame to grow on the right if necessary
        buttonFrame.grid_columnconfigure(col, weight=1)

        if gridButtonFrame:
            buttonFrame.grid(row=0, column=4)
        self.doDeltaMenu()
    
        self.enableButtons()
    
    def cmdCancel(self, cmd):
        if self.currCmd:
            self.currCmd.abort()
    
    def cmdDone(self, *args, **kargs):
        self.currCmd = None
        self.enableButtons()
        
    def doDeltaBtn(self, btn):
        """Called by the +/- buttons to offset the focus.
        """
        deltaMagStr = self.deltaMenu.getString().split()[0]
        deltaFocus = float(btn["text"] + deltaMagStr)
        cmdVar = self.createFocusCmd(deltaFocus, isIncr=True)
        self.runFocusCmd(cmdVar)

    def doDeltaMenu(self, wdg=None):
        """Called by the focus increment menu to adjust the increment."""
        incr = self.deltaMenu.getString()
        self.decreaseButton.helpText = "Decrease %s focus by %s" % (self.name, incr)
        self.increaseButton.helpText = "Increase %s focus by %s" % (self.name, incr)
    
    def doSet(self, btn=None):
        """Called by the Set... button to set a new focus value."""
        currFocus, isCurrent = self.currFocusWdg.get()
        if isCurrent and currFocus != None:
            default = currFocus
        else:
            default = None

        newFocus = FocusSetDialog(self, default).result
        if newFocus == None:
            return
        cmdVar = self.createFocusCmd(newFocus, isIncr=False)
        self.runFocusCmd(cmdVar)
    
    def startTimer(self, predTime, elapsedTime=0):
        """Display move timer."""
        self.timerWdg.grid()
        self.timerWdg.start(value=predTime, newMax = predTime)
    
    def endTimer(self, dumValue=None, isCurrent=True, keyVar=None):
        """Hide move timer. May be a keyword variable callback."""
        if isCurrent:
            self.timerWdg.clear()
            self.timerWdg.grid_remove()
    
    def createFocusCmd(self, newFocus, isIncr=False):
        """Create and return a focus command.
        This method must be subclassed.
        """
        raise NotImplementedError("Subclass must define")
    
    def enableButtons(self, wdg=None):
        cmdRunning = self.currCmd and not self.currCmd.isDone()
        self.setButton.setEnable(not cmdRunning)
        self.decreaseButton.setEnable(not cmdRunning)
        self.increaseButton.setEnable(not cmdRunning)
        self.cancelButton.setEnable(cmdRunning)
    
    def runFocusCmd(self, cmdVar):
        """Execute the focus command that was created by createFocusCmd"""
        cmdVar.addCallback(
            self.cmdDone,
            callTypes = RO.KeyVariable.DoneTypes,
        )
        self.currCmd = cmdVar
        self.statusBar.doCmd(cmdVar)
        self.enableButtons()
        
    def updFocus(self, newFocus, isCurrent=True, **kargs):
        """Called when new focus seen.
        """
        self.currFocusWdg.set(newFocus, isCurrent=isCurrent)


class FocusSetDialog(RO.Wdg.ModalDialogBase):
    def __init__(self, master, initValue):
        self.initValue = float(initValue)

        RO.Wdg.ModalDialogBase.__init__(self,
            master,
            title="Set Focus",
        )

    def body(self, master):
        l = Tkinter.Label(master, text="New Secondary Focus:")
        l.pack(side="top", anchor="w")
        
        valFrame = Tkinter.Frame(master)
        
        self.valWdg = RO.Wdg.FloatEntry(valFrame,
            defValue = self.initValue,
            defMenu = "Default",
            helpText = "secondary focus offset",
        )
        if RO.TkUtil.getWindowingSystem() == RO.TkUtil.WSysAqua:
            # work around tk bug 1101854
            self.valWdg.unbind("<<CtxMenu>>")
        self.valWdg.selectAll()
        self.valWdg.pack(side="left")
        u = Tkinter.Label(valFrame,
            text=RO.StringUtil.MuStr + "m",
        )
        u.pack(side="left")
        valFrame.pack(side="top", anchor="w")
        
        s = RO.Wdg.StatusBar(master)
        s.pack(side="top", expand=True, fill="x")
        
        self.okWdg.helpText = "Set secondary focus"
        self.cancelWdg.helpText = "Cancel"
        
        return self.valWdg
    
    def setResult(self):
        self.result = self.valWdg.getNumOrNone()


if __name__ == "__main__":
    root = RO.Wdg.PythonTk()
    
    class TestFocusWdg(FocusWdg):
        def __init__(self, master, statusBar):
            FocusWdg.__init__(self,
                master,
                name = "test",
                statusBar = statusBar,
                increments = (25, 50, 100),
                defIncr = 50,
                helpURL = None,
                label = "Focus",
            )
            
        def createFocusCmd(self, newFocus, isIncr=False):
            if isIncr:
                verbStr = "relfocus"
            else:
                verbStr = "focus"
            cmdStr = "%s=%s" % (verbStr, newFocus)
    
            return RO.KeyVariable.CmdVar (
                actor = "test",
                cmdStr = cmdStr,
            )

    tuiModel = TUI.TUIModel.getModel(True)
    kd = tuiModel.dispatcher
    statusBar = RO.Wdg.StatusBar(
        master = root,
        dispatcher = tuiModel.dispatcher,
        prefs = tuiModel.prefs,
        playCmdSounds = True,
    )
    sfw = TestFocusWdg(root, statusBar = statusBar)
    sfw.pack()
    statusBar.pack(expand=True, fill="x")

    root.mainloop()
