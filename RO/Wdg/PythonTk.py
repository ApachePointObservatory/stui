#!/usr/local/bin/python
"""
A wrapper around Tkinter.Tk that puts up a separate Python
debugging window and then returns root. Optionally reads options
from a specified options file.

Instead of using an options file, you may wish to have a look
at the RO.Prefs module. It offers graphical editing of preferences
with live updating.

History:
2002-01-29 ROwen    Added code to allow global changing of fonts. This is a
    preliminary implementation, in that it doesn't mesh well with user
    setting of the option database, nor is there any other way to read
    in user defaults. Removed "from Tkinter import *".
2002-07-30 ROwen    Moved into the RO.Wdg module and renamed from ROStdTk.
2002-07-31 ROwen    Cleaned out a bunch of obsolete code.
2003-06-18 ROwen    Modified to test for StandardError instead of Exception
2004-05-18 ROwen    Stopped importing sys and tkFont since they weren't used.
2004-06-22 ROwen    Renamed ScriptTk->PythonTk to avoid confusion with ScriptWdg.
                    Modified to use renamed ScriptWindow->PythonWdg module.
2004-08-11 ROwen    Define __all__ to restrict import.
2004-09-14 ROwen    Modified import of Bindings to not import RO.Wdg.
"""
__all__ = ['PythonTk']

import Tkinter
import Bindings
import PythonWdg

class PythonTk (Tkinter.Tk):
    """Creates a Tkinter application with standard menus and such"""
    def __init__(self, **kargs):
        """Creates a new application with some standard menus and such
        Returns the root window, just like Tk()
        To use:
            import RO.Wdg
            myApp = RO.Wdg.PythonTk()
            # configure stuff here, e.g. creating new windows, etc.
            myApp.mainloop()

        Keyword arguments:
            All those for Tkinter.Tk(), plus:
            "optionfile": the full path name of an option file
        """

        # first parse PythonTk-specific options
        # but do not try to apply them yet if they require Tk to be initialized
        optionfile = None
        if kargs and kargs.has_key("optionfile"):
            optionfile = kargs["optionfile"]
            del(kargs["optionfile"])

        # basic initialization
        Tkinter.Tk.__init__(self, **kargs)
        
        # if the user supplied an option file, load it
        if optionfile:
            try:
                self.option_readfile(optionfile)
            except StandardError, e:
                print "cannot read option file; error:", e
        
        # create and display a Python script window
        self.pyToplevel = Tkinter.Toplevel()
        self.pyToplevel.geometry("+0+450")
        self.pyToplevel.title("Python")
        pyFrame = PythonWdg.PythonWdg(self.pyToplevel)
        pyFrame.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
        
        # set up standard bindings
        Bindings.stdBindings(self)


if __name__ == "__main__":
    root = PythonTk()
    aText = Tkinter.Text(root, width=30, height=2)
    aText.insert(Tkinter.END, "some text to manipulate")
    aText.grid(row=0, column=0, sticky=Tkinter.NSEW)
    anEntry = Tkinter.Entry(root)
    anEntry.insert(0, "more text")
    anEntry.grid(row=1, column=0, sticky=Tkinter.EW)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.mainloop()
