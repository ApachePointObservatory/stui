"""
Base class for a widget to control a particular device, such as a shutter
"""
import contextlib
import Tkinter
import RO.Wdg
import opscore.actor.keyvar

class BaseDeviceWdg(Tkinter.Frame):
    """Base class for widget to command a device
    
    Derived classes should:
    - Override enableWdg and call the base class's version
    - Pack or grid self.cancelBtn
    - Call doCmd to issue commands
    """
    actor = "apogeecal"
    def __init__(self, master, actor, statusBar, helpURL=None):
        Tkinter.Frame.__init__(self, master)
        self.actor = actor
        self.statusBar = statusBar
        self.helpURL = helpURL

        self.currCmd = None
        self.settingStatus = False
        
        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "X",
            callFunc = self.doCancel,
            helpText = "Cancel command",
            helpURL = helpURL,
        )

    def doCancel(self, wdg=None):
        """Cancel the current command, if any
        """
        if self.isRunning:
            self.currCmd.abort()

    def doCmd(self, cmdStr):
        """Start a command
        
        Ignored if updating status.
        Raise RuntimeError if a command is already being executed
        """
        if self._updatingStatus:
            return
            
        if self.isRunning:
            raise RuntimeError("A command is already running")

        self.currCmd = opscore.actor.keyvar.CmdVar(
            actor = self.actor,
            cmdStr = cmdStr,
            callFunc = self._cmdCallback,
        )
        self.statusBar.doCmd(self.currCmd)
        self.enableButtons()

    def enableButtons(self, dumCmd=None):
        """Enable or disable widgets, as appropriate
        
        Derived classes should override this method
        and should either handle cancelBtn or call this method to do it.
        """
        self.cancelBtn.setEnable(self.isRunning)
    
    def updateStatus(self, dumArg=None):
        """Update status based on current values of keywords.
        
        Derived classes must:
        - Override this method
        - Put all code within "with self.updateLock()", e.g.:
            with self.updateLock():
                # do stuff here
        """
        raise NotImplementedError()
    
    @property
    def updatingStatus(self):
        """Return True if updating status
        """
        return self._updatingStatus
    
    @contextlib.contextmanager
    def updateLock(self):
        """Use in a with statement while updating status
        
        This prevents doCmd from executing in reaction to anything done by updateStatus,
        for instance changing Checkbuttons.
        """
        try:
            self._updatingStatus = True
            yield
        finally:
            self._updatingStatus = False

    @property
    def isRunning(self):
        """Return True if running a command
        """
        return self.currCmd and not self.currCmd.isDone
    
    def _cmdCallback(self, cmdVar):
        """Command callback

        If the command was aborted or failed then restore the current state.
        Update button state.
        """
        if cmdVar.didFail:
            self.updateStatus()
        self.enableButtons()
