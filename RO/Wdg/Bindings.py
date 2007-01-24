#!/usr/bin/env python
"""Sets up standard key bindings for each platform.
Supplements Tk's defaults and handles readonly text widgets.

Note: good emulation for Entry and Text on Mac (and probably on Windows) is tricky
because the insertion cursor and the selection are separate entities
and can have unrelated values. Thus extending the current selection
in a Mac-like way is difficult.

2003-02-27 ROwen    Fixed read only to allow keyboard shortcuts
        for copy and select all. Fixed Select All bindings for Mac OS X
        and removed unneeded bindings for Cut, Copy and Paste.
        I think the Mac had been set up for unix (X windows) Tk
        instead of aqua Tk, from the days when there was no choice.
2003-03-28 ROwen    Fixed platform detection for unix and windows;
        also ditched <<Paste-Selection>> on Mac and Windows
        since it interferes with standard button use on those platforms.
2003-04-08 ROwen    Finally figured out how to stop <ButtonRelease-2>
        on MacOS X from pasting the selection.
2003-04-15 ROwen    Added event <<CtxMenu>>.
2003-04-22 ROwen    Fixed Mac <<CtxMenu>> key bindings to support control-click;
        improved unix <<CtxMenu>> to allow control-click of any-button.
2004-05-18 ROwen    Added right-click for unix <<CtxMenu>>.
                    Added stopEvent and mod. existing code to use it.
2004-08-11 ROwen    Define __all__ to restrict import.
2005-06-17 ROwen    Modified stdBindings to use TkUtil. Also, may have improved
                    stdBindings's disabling of <<Paste-Selection>> on Windows.
                
2005-06-27 ROwen    Removed unused import of sys.
2005-07-07 ROwen    Modified for moved RO.TkUtil.
2005-07-14 ROwen    Fixed bug in makeReadOnly: was not trappling button-release-2
                    (which pastes the selection, at least on unix).
2005-08-05 ROwen    Commented out a diagnostic print statement in stopEvent.
2005-09-16 ROwen    Bug fix on Mac: Command-Q and Command-W were ignored.
                    Similar fixes may be needed on unix and/or windows.
"""
__all__ = ['makeReadOnly', 'stdBindings', 'stopEvent']

import Tkinter
import RO.TkUtil

def doQuit(evt):
    evt.widget.quit()

def doWithdraw(evt):
    evt.widget.winfo_toplevel().wm_withdraw()

# a dictionary of application events
# so far I only know the entries for MacOS X
AppEventDict = {
    RO.TkUtil.WSysAqua: (
        ("<Command-Key-q>", doQuit),
        ("<Command-Key-w>", doWithdraw),
    ),
}   

def makeReadOnly(tkWdg):
    """Makes a Tk widget (typically an Entry or Text) read-only,
    in the sense that the user cannot modify the text (but it can
    still be set programmatically). The user can still select and copy text
    and key bindings for <<Copy>> and <<Select-All>> still work properly.
    
    Inputs:
    - tkWdg: a Tk widget
    """
    def doCopy(evt):
        tkWdg.event_generate("<<Copy>>")

    def doSelectAll(evt):
        tkWdg.event_generate("<<Select-All>>")

    # kill all events that can change the text,
    # including all typing (even shortcuts for
    # copy and select all)
    tkWdg.bind("<<Cut>>", stopEvent)
    tkWdg.bind("<<Paste>>", stopEvent)
    tkWdg.bind("<<Paste-Selection>>", stopEvent)
    tkWdg.bind("<<Clear>>", stopEvent)
    tkWdg.bind("<Key>", stopEvent)
    tkWdg.bind("<ButtonRelease-2>", stopEvent)
    
    # restore copy and select all
    for evt in tkWdg.event_info("<<Copy>>"):
        tkWdg.bind(evt, doCopy)
    for evt in tkWdg.event_info("<<Select-All>>"):
        tkWdg.bind(evt, doSelectAll)
    
    # restore other behaviors
    # note: binding specific events avoids introducing
    # events that might cause editing (for example some control keys)
    winSys = RO.TkUtil.getWindowingSystem()
    appEvents = AppEventDict.get(winSys, ())
    for eventName, func in appEvents:
        tkWdg.bind(eventName, passEvent)

def stdBindings(root, debug=False):
    """Sets up standard key bindings for each platform"""
    
    btnNums = RO.TkUtil.getButtonNumbers()
    winSys = RO.TkUtil.getWindowingSystem() 

    # platform-specific bindings
    if winSys == RO.TkUtil.WSysX11:
        # unix
        if debug:
            print "Unix/x11 key bindings"
        root.event_add("<<CtxMenu>>", "<Control-Button-1>")
        root.event_add("<<CtxMenu>>", "<Control-Button-2>")
        root.event_add("<<CtxMenu>>", "<Control-Button-3>")
    else:
        if winSys == RO.TkUtil.WSysAqua:
            if debug:
                print "Mac Aqua key bindings"
            root.event_add("<<Select-All>>", "<Command-Key-a>")
            root.bind_class("Entry", "<Key-Up>", _entryGoToLeftEdge)
            root.bind_class("Entry", "<Key-Down>", _entryGoToRightEdge)
            root.bind_class("Entry", "<Command-Key-Left>", _entryGoToLeftEdge)
            root.bind_class("Entry", "<Command-Key-Right>", _entryGoToRightEdge)
        else:
            if debug:
                print "Windows key bindings"
            root.event_add("<<Select-All>>", "<Control-Key-a>")
        
        """Disable <<Paste-Selection>>
        
        By default Tkinter uses <ButtonRelease-2> to paste the selection
        on the Mac this is reserved for bringing up a contextual menu.
        Unfortunately, I'm not sure where this event is bound;
          it is not bound to the Entry, Text or Widget classes.
          It's almost as if it's written into the window manager
          or something equally inaccessible.

        Anyway, without knowing that I couldn't just unbind
        an existing event. Instead I had to bind a new method stopEvent
        to stop the event from propogating.
        
        Using bind_all to stopEvent did not work; apparently the
        normal binding is run first (so it must be at the class level?)
        before the all binding is run. Sigh.
        """
        root.bind_class("Entry", "<ButtonRelease-2>", stopEvent)
        root.bind_class("Text", "<ButtonRelease-2>", stopEvent)
        # Entry and Text do have <Button-2> bindings;
        # they don't actually seem to do any harm
        # but I'd rather not risk it
        root.unbind_class("Entry", "<Button-2>")
        root.unbind_class("Text", "<Button-2>")

    # bind right button to <<CtxMenu>>
    root.event_add("<<CtxMenu>>", "<Button-%d>" % btnNums[2])

    # virtual event bindings (common to all platforms)
    # beyond the default <<Cut>>, <<Copy>> and <<Paste>>
    root.bind_class("Text", "<<Select-All>>", _textSelectAll)
    root.bind_class("Entry", "<<Select-All>>", _entrySelectAll)
    
    # application events
    appEvents = AppEventDict.get(winSys, ())
    for eventName, func in appEvents:
        root.bind_all(eventName, func)
    
def stopEvent(evt):
    """stop an event from propogating"""
    #print "stopped an event"
    return "break"

def passEvent(evt):
    """allow an event to propogate"""
    return

def _textSelectAll(evt):
    """Handles <<Select-All>> virtual event for Text widgets.
    The - 1 char prevents adding an extra \n at the end of the selection"""
    evt.widget.tag_add("sel", "1.0", "end - 1 char")
    
def _entrySelectAll(evt):
    """Handles <<Select-All>> virtual event for Entry widgets."""
    evt.widget.selection_range("0", "end")

def _entryGoToLeftEdge(evt):
    """Moves the selection cursor to the left edge"""
    evt.widget.icursor(0)

def _entryGoToRightEdge(evt):
    """Moves the selection cursor to the right edge"""
    evt.widget.icursor("end")

if __name__ == "__main__":
    root = Tkinter.Tk()
    stdBindings(root, debug=1)
    
    t = Tkinter.Text(root, width=20, height=5)
    tr = Tkinter.Text(root, width=20, height=5)
    tr.insert("end", "here is some test text for the read only text widget")
    makeReadOnly(tr)
    e = Tkinter.Entry(root)
    t.pack()
    tr.pack()
    e.pack()
    
    
    root.mainloop()
