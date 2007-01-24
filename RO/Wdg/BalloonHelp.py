#!/usr/bin/env python
"""Simple implementation of pop-up help.

Simply call enableBalloonHelp to activate help application-wide.

To do:
- Improve AI for old vs recent logic for how long to wait to show help.
  - If help is showing and I mouse into a widget with no help, keep updating the hide time (so the wait is short) for each motion.
   - If I type, do not keep updating, because I have intentionally hidden the help.

- On MacOS X (and perhaps Windows?) make the popped up window NOT get focus. Right now if you click on a field to enter data, when help is shown the focus shifts to the help window, so the first keystroke is lost in getting rid of the window. Very frustrating! This appears to be a bug in Aqua Tk 8.4.2 (since it does not occur under unix) and I have reported it. Note that Tck is convinced that the original widget still has focus. Even generating a keyboard event and sending it directly to the original widget fails horribly--the event is actually sent to the help window, which generates a new event...infinite loop.

- Is there any way to make help appear when a modifier is pressed? I don't think so, because there is no "mouse within" event. One can hold the modifier and wiggle the mouse a bit, but that does not feel natural.
- Consider using pop-ups for menus and status bars for everything else? Or pop-ups for read-only controls and menus and status bars for entry widgets.
- Consider one central help window that the user can show or hide. Harder to see but works for menus and etc and is easily hidden.

History:
2004-08-11 ROwen    Define __all__ to restrict import.
"""
__all__ = ['enableBalloonHelp']

import Tkinter
import time

_HelpObj = None

class _BalloonHelp:
    def __init__(self, delayMS = 600):
        self.focusWdg = None
        self.msgWin = Tkinter.Toplevel()
        self.msgWin.overrideredirect(True)
        self.msgWdg = Tkinter.Message(self.msgWin, bg="light yellow")
        self.msgWdg.pack()
        self.msgWin.withdraw()
        self.timer = ""
        self.msgWdg.bind_all('<Motion>', self.start)
        def stopAndUpdTime(evt):
            self.updTime()
            self.stop(evt)
        self.msgWdg.bind_all('<Leave>', stopAndUpdTime)
        self.msgWdg.bind_all('<ButtonPress>', self.stop)
        self.msgWdg.bind_all('<KeyPress>', self.stop)
        self.msgWdg.bind_all('<Tab>', self.stop, add=True)
        self.delayMS = delayMS
        self.lastTime = 0
    
    def updTime(self):
        """If help showing or current time soon after lastTime then:
        - updates lastTime
        - returns True
        else leaves lastTime alone and returns False
        """
        currTime = time.time()
        if currTime < self.lastTime + 1 or self.msgWin.winfo_ismapped():
            self.lastTime = currTime
            return True
        return False
        
    def start(self, evt):
        """Start a timer to show the help in a bit,
        or if the help window is already showing,
        redisplay it immediately"""
        isFast = self.updTime()
        self.stop()
        try:
            if evt.widget.helpText:
                if isFast:
                    dtime = 100
                else:
                    dtime = self.delayMS
                self.timer = self.msgWin.after(dtime, self.show, evt)
        except AttributeError:
            pass
    
    def stop(self, evt=None):
        """Stop the timer and hide the help"""
        if self.timer:
            self.msgWin.after_cancel(self.timer)
            self.timer = ""
        self.msgWin.withdraw()
    
    def show(self, evt):
        """Show help"""
        self.msgWin.withdraw()
        x, y = evt.x_root, evt.y_root
        self.msgWin.geometry("+%d+%d" % (x+10, y+10))
        self.msgWdg["text"] = evt.widget.helpText
        self.msgWdg.update_idletasks() # let the geometry manager move and resize the window
        self.msgWin.tkraise()
        self.msgWin.deiconify()

def enableBalloonHelp(delayMS = 1000):
    global _HelpObj
    if _HelpObj:
        _HelpObj.delayMS = delayMS
    else:
        _HelpObj = _BalloonHelp(delayMS)


if __name__ == '__main__':
    import OptionMenu
    root = Tkinter.Tk()
    
    l0 = Tkinter.Label(text="Data")
    l0.grid(row=0, column=0, sticky="e")
    l0.helpText = "Help for the Data label"
    e0 = Tkinter.Entry(width=10)
    e0.helpText = "Help for the data entry widget"
    e0.grid(row=0, column=1)
    l1 = Tkinter.Label(text="No Help")
    l1.grid(row=1, column=0)
    e1 = Tkinter.Entry(width=10)
    e1.grid(row=1, column=1)
    l2 = Tkinter.Label(text="Option Menu")
    l2.helpText = "Help for the option menu label"
    l2.grid(row=2, column=0)
    m2 = OptionMenu.OptionMenu(root,
        items = ("Item 1", "Item 2", "Etc"),
        defValue = "Item 1",
        helpText = "Help for the menu button",
    )
    m2.grid(row=2, column=1)

    ph = enableBalloonHelp()
    
    root.mainloop()
