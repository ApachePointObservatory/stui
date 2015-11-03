#!/usr/bin/env python
"""General focus control.

To do: improve placement of countdown timer. Right now it works fine for Secondary Focus but probably not
for the NA2 Guider. But first see if the obs specs are comfortable with the NA2 Guider gmech controls.

History:
2008-02-04 ROwen
2008-02-11 ROwen    Modified to always show the cancel button (now named X instead of Cancel).
2008-02-13 ROwen    Fix PR 738: removed focus limits, since they were only a guess and getting it wrong
                    could put unreasonable limits on the user. Let the actor handle focus limits.
2009-04-01 ROwen    Modified to use new TUI.Base.Wdg.StatusBar.
2010-03-12 ROwen    Removed unused import.
2010-06-28 ROwen    Removed duplicate import (thanks to pychecker).
2011-05-03 ROwen    Change name to descr and set help to desrc instead of name + " focus"
                    Allow float and string values for increments and defIncr.
                    Bug fix: had label and currLabel but the former was ignored. Now use only label.
                    Bug fix: the dialog box always said Set Focus, ignoring descr.
                    Bug fix: the dialog box always used microns, ignoring units.
2011-05-04 ROwen    Made the label widget and units widget both accessible.
                    Bug fix: self.label was not present in FocusWdg.
                    Bug fix: label was misused in the dialog box.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import Tkinter
import RO.Wdg
import RO.TkUtil
import RO.StringUtil
import opscore.actor.keyvar
import TUI.Base.Wdg

__all__ = ["FocusWdg"]

MicronStr = RO.StringUtil.MuStr + "m"

class FocusWdg(Tkinter.Frame):
    def __init__ (self,
        master,
        label = "Focus",
        statusBar = None,
        increments = None,
        defIncr = None,
        helpURL = None,
        formatStr = "%.1f",
        units = MicronStr,
        descr = None,
        focusWidth = 5,
        buttonFrame = None,
     **kargs):
        """A widget for displaying and specifying focus.
        
        Subclasses must override createFocusCmd and must call startTimer, endTimer and updFocus

        Inputs:
        - master        master Tk widget -- typically a frame or window
        - statusBar     an import TUI.Base.StatusBar widget
        - label         text for current focus label
        - increments    focus increments (ints) for menu; defaults to 25, 50, 100
        - defIncr       default focus increment (int); defaults to increments[2]
        - formatStr     format for displaying focus
        - units         units of focus
        - descr         brief description of device whose focus is being adjusted; used for help;
                        defaults to label.lower()
        - focusWidth    width of focus input or output field
        - buttonFrame   button frame; if omitted then the buttons are shown right of the current focus
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        if not increments:
            increments = (25, 50, 100)
        if not defIncr:
            defIncr = int(increments[1])

        self.label = label
        self.units = units
        if descr is None:
            descr = label.lower()
        self.descr = descr
        self.statusBar = statusBar
        self.formatStr = formatStr
        self.focusWidth = focusWidth

        self.currCmd = None

        # current focus display
        self.labelWdg = RO.Wdg.Label(master=self, text=label)
        self.labelWdg.grid(row=0, column=0)

        self.currFocusWdg = RO.Wdg.FloatLabel(
            master = self,
            formatStr = self.formatStr,
            width = self.focusWidth,
            helpText = "Current %s" % (self.descr,),
            helpURL = helpURL,
        )
        self.currFocusWdg.grid(row=0, column=1)
        self.unitsWdg = RO.Wdg.StrLabel(
            master = self,
            text = self.units,
        )
        self.unitsWdg.grid(row=0, column=2)

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
        if buttonFrame is None:
            gridButtonFrame = True
            buttonFrame = Tkinter.Frame(self)
        else:
            gridButtonFrame = False
            
        col = 0
                
        self.setButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Set...",
            callFunc = self.doSet,
            helpText = "Set %s" % (self.descr,)
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
        
        incrStrs = ["%s %s" % (incr, self.units) for incr in increments]
        defIncrStr = "%s %s" % (defIncr, self.units)
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
        self.decreaseButton.helpText = "Decrease %s by %s" % (self.descr, incr)
        self.increaseButton.helpText = "Increase %s by %s" % (self.descr, incr)
    
    def doSet(self, btn=None):
        """Called by the Set... button to set a new focus value."""
        currFocus, isCurrent = self.currFocusWdg.get()
        if isCurrent and currFocus is not None:
            default = currFocus
        else:
            default = None

        newFocus = FocusSetDialog(
        	master = self,
        	label = self.label,
        	initValue = default,
        	formatStr = self.formatStr,
        	focusWidth = self.focusWidth,
        	descr = self.descr,
        	units = self.units,
        ).result
        if newFocus is None:
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
        cmdRunning = self.currCmd and not self.currCmd.isDone
        self.setButton.setEnable(not cmdRunning)
        self.decreaseButton.setEnable(not cmdRunning)
        self.increaseButton.setEnable(not cmdRunning)
        self.cancelButton.setEnable(cmdRunning)
    
    def runFocusCmd(self, cmdVar):
        """Execute the focus command that was created by createFocusCmd"""
        cmdVar.addCallback(
            self.cmdDone,
            callCodes = opscore.actor.keyvar.DoneCodes,
        )
        self.currCmd = cmdVar
        self.statusBar.doCmd(cmdVar)
        self.enableButtons()
        
    def updFocus(self, keyVar):
        """Called when new focus seen.
        """
        self.currFocusWdg.set(keyVar[0], isCurrent=keyVar.isCurrent)


class FocusSetDialog(RO.Wdg.ModalDialogBase):
    def __init__(self, master, label, initValue, formatStr, focusWidth, descr, units):
    	"""Create a new "set focus" dialog.
    	
    	Inputs:
    	- master: master Tk widget
    	- label: word for title
    	- initValue: initial focus value
    	- formatStr: format for focus entry
    	- focusWidth: width of focus entry, in characters
    	- descr: brief description of item, for help
    	- units: units of value
    	"""
    	self.label = label
    	self.descr = descr
    	if initValue is None:
    		initValue = 0
        self.initValue = float(initValue)
        self.formatStr = formatStr
        self.focusWidth = int(focusWidth)
        self.units = units

        RO.Wdg.ModalDialogBase.__init__(self,
            master,
            title="Set %s" % (self.label,),
        )

    def body(self, master):
        l = Tkinter.Label(master, text="New %s:" % (self.label,))
        l.pack(side="top", anchor="w")
        
        valFrame = Tkinter.Frame(master)
        
        self.valWdg = RO.Wdg.FloatEntry(
            master = valFrame,
            defValue = self.initValue,
            defFormat = self.formatStr,
            width = self.focusWidth,
            defMenu = "Default",
            helpText = "%s offset" % (self.descr,),
        )
        if RO.TkUtil.getWindowingSystem() == RO.TkUtil.WSysAqua:
            # work around tk bug 1101854
            self.valWdg.unbind("<<CtxMenu>>")
        self.valWdg.selectAll()
        self.valWdg.pack(side="left")
        u = Tkinter.Label(master = valFrame, text=self.units)
        u.pack(side="left")
        valFrame.pack(side="top", anchor="w")
        
        self.okWdg.helpText = "Set %s"  % (self.descr,)
        self.cancelWdg.helpText = "Cancel"
        
        return self.valWdg
    
    def setResult(self):
        self.result = self.valWdg.getNumOrNone()


if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot
    
    class TestFocusWdg(FocusWdg):
        def __init__(self, master, statusBar):
            FocusWdg.__init__(self,
                master,
                descr = "test",
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
    
            return opscore.actor.keyvar.CmdVar (
                actor = "test",
                cmdStr = cmdStr,
            )

    statusBar = TUI.Base.Wdg.StatusBar(
        master = root,
        playCmdSounds = True,
    )
    sfw = TestFocusWdg(root, statusBar = statusBar)
    sfw.pack()
    statusBar.pack(expand=True, fill="x")

    tuiModel.reactor.run()
