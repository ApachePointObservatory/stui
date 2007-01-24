#!/usr/bin/env python
"""Entry widget for commands, with history.

History:
2002-11-13 ROwen    Added history. Bug fix: entering a command would not
                    scroll all the way to the bottom if data was coming in; fixed using
                    a carefully placed update_idletasks (we'll see if this always works).
                    Bug fix: command history recall appended an extra character
                    to the end of the recalled command; fixed by not propogating key events.
2002-11-15 ROwen    Fixed the example by specifying an initial window geometry
                    and updated the comments to explain why this is necessary
2002-12-05 ROwen    Added support for URL-based help
2003-03-07 ROwen    Changed RO.Wdg.StringEntry to RO.Wdg.StrEntry.
2003-04-15 ROwen    Removed unused import of CtxMenu.
2004-05-18 ROwen    Bug fix: didn't set self.cmdText if no helpURL.
                    Stopped importing sys since it was not being used.
2004-07-16 ROwen    Deleted redundant method showCmd.
                    Added support for the user's command being rejected
                    by the command callback function.
                    Renamed all event handlers, including adding a leading _
                    to make it clear they are internal functions
                    and to avoid name collisions with subclasses.
2004-08-11 ROwen    Define __all__ to restrict import.
2004-08-25 ROwen    Removed support for user's command being rejected. It was confusing to users.
2004-09-14 ROwen    Tweaked the imports.
2006-02-22 ROwen    Split off from CmdReplyWdg.
"""
__all__ = ['CmdWdg']

import Tkinter
import Entry

class CmdWdg (Entry.StrEntry):
    """Entry field for one-line text commands, with history.
    
    Special keys:
    - <return>: execute current text (one or more \n-separated commands)
    - <up-arrow> or <control-p>: go backwards in history
    - <down-arrow> or <control-n>: go forwards in history

    Inputs:
    - cmdFunc: called when <return> is pressed in the command entry window;
        takes one argument: cmdStr, a command to execute
        note: cmdStr does not have a terminating <newline>
    - maxCmds: the maximum # of commands to save in the command history buffer
    - helpURL: the URL of a help page
    """
    def __init__ (self,
        master,
        cmdFunc,
        maxCmds=50,
        helpURL = None,
    **kargs):
        Entry.StrEntry.__init__(self,
            master = master,
            helpURL = helpURL,
        **kargs)
        
        self.cmdHistory = []
        
        self.cmdFunc = cmdFunc

        self.histIndex = -1
        self.maxCmds = int(maxCmds)
        self.currText = "" # allows users to look back in history without losing the current text
        self.pendingCmds = []

        self.cmdVar = self.getVar()

        self.bind('<KeyPress-Return>', self._doCmd)
        self.bind('<KeyPress-Up>', self._doHistUp)
        self.bind('<Control-p>', self._doHistUp)
        self.bind('<KeyPress-Down>', self._doHistDown)
        self.bind('<Control-n>', self._doHistDown)
    
    def clear(self):
        """Clear display"""
        Entry.StrEntry.clear(self)
        self.currText = ""
    
    def _doCmd(self, evt=None):
        """Start executing the current command or \n-separated commands.
        """
        cmdStr = self.get()
        self.clear()

        # insert command in history (if not blank and not a copy of the most recent command)
        # and reset the history index
        if cmdStr:
            if (not self.cmdHistory) or (cmdStr != self.cmdHistory[0]):
                self.cmdHistory.insert(0, cmdStr)
        self.histIndex = -1

        # purge excess commands, if any
        del(self.cmdHistory[self.maxCmds:])
        
        # execute command callback
        # (do this last in case it fails)
        if self.cmdFunc:
            self.cmdFunc(cmdStr)
    
    def _doHistDown(self, *args, **kargs):
        """Go down one place in the history index;
        if at the bottom, then:
        - if a current command was tempoarily saved, redisplay it
        - otherwise do nothing
        """
        if self.histIndex > 0:
            self.histIndex -= 1
            self.set(self.cmdHistory[self.histIndex])
            self.icursor(Tkinter.END)
        elif self.histIndex == 0:
            self.set(self.currText)
            self.histIndex = -1
            self.icursor(Tkinter.END)
        return "break" # prevent event from being propogated            
    
    def _doHistUp(self, *args, **kargs):
        """Go up one place in the history index.
        If at the top, display a blank line.
        """
        if self.histIndex == -1:
            # current command is showing; save it (but not in the history buffer),
            # so it can be retrieved with down-arrow or discarded by issuing some other cmd
            self.currText = self.get()

        # if there is a next command up, index and retrieve it
        # else clear the line
        if self.histIndex < len(self.cmdHistory) - 1:
            self.histIndex += 1
            self.set(self.cmdHistory[self.histIndex])
            self.icursor(Tkinter.END)
        else:
            self.histIndex = len(self.cmdHistory)
            self.set("")
        return "break" # prevent event from being propogated            

    def _showKeyEvent(self, evt):
        """Show the details of a keystroke; for debugging and development.
        """
        print "Key event=%r" % (evt.__dict__, )
    
    

if __name__ == "__main__":
    from RO.Wdg.PythonTk import PythonTk
    import random
    root = PythonTk()
    
    FailCmd = 'fail'

    def doCmd(cmdStr):
        if cmdStr == FailCmd:
            raise RuntimeError("%r triggers the error test" % cmdStr)
        print "Cmd = %r" % cmdStr

    testFrame = CmdWdg (root,
        cmdFunc=doCmd,
        width = 40,
    )
    testFrame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

    root.mainloop()
