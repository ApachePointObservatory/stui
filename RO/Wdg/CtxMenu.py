#!/usr/local/bin/python
"""Add contextual menu to a Tkinter widget, including automatic
support for help.

Note: to see the menus you must issue a <<CtxMenu>> event,
e.g. by running RO.Wdg.Bindings.stdBindings(wdg).

History:
2002-11-26 ROwen    Added helpURL support.
2003-03-21 ROwen    Fixed getURL to use urlparse.urljoin.
2003-03-27 ROwen    Fixed platform detection for unix and windows.
2003-04-02 ROwen    Added insertCtxMenuCommand and insertCtxMenuSeparator.
2003-04-15 ROwen    Totally overhauled to use ctxConfigMenu to set up the menu,
                    permitting dynamic ctx menus and simplifying the code;
                    removed helpText (supports only helpURL);
                    modified to use the <<CtxMenu>> event to raise the ctx menu.
2003-04-22 ROwen    Print the error message if a help URL cannot be opened.
2004-05-18 ROwen    Stopped importing sys and Dialog since they weren't used.
2004-05-21 ROwen    Bug fix: ctxShowHelp was not catching exceptions
                    when a URL could not be opened on MacOS X aqua.
                    This made it hard to see what URL had failed.
                    Enhancement: if ctxShowHelp cannot show a file:
                    URL with an anchor, try again without the anchor
                    (for instance MacOS X 10.3)
2004-07-20 ROwen    Modified to allow adding a contextual menu
                    to a widget that already is or has a contextual menu.
2004-08-11 ROwen    Modified to use Constants for URL help base.
                    Define __all__ to restrict import.
2004-09-03 ROwen    Modified for RO.Wdg.st_... -> RO.Constants.st_...
2004-09-14 ROwen    Bug fix to test code.
                    Removed unused global _HelpURLBase (moved to RO.Constants).
                    Minor change to CtxMenu to make pychecker happier.
2004-10-05 ROwen    Modified to open HTML help in a background thread.
2004-10-13 ROwen    Removed unused import of urlparse and webbrowser.
2005-06-03 ROwen    Fixed minor indentation oddity (one tab-space).
2005-06-08 ROwen    Changed CtxMenu to a new style class.
"""
__all__ = ['CtxMenu', 'CtxMenuMixin', 'addCtxMenu']

import Tkinter
import RO.Comm.BrowseURL
import RO.Constants
import RO.OS

class CtxMenu(object):
    def __init__(self,
        wdg=None,
        helpURL=None,
        configFunc = None,
        doTest = True,
    ):
        """Add a contextual menu to a Tkinter widget.
        
        Inputs:
        - wdg:  the widget to which to bind the means of bringing up the menu.
            - To add a contextual menu to a specific Tkinter widget, set wdg = the widget
              and be sure to save a reference to the returned object. Or use addCtxMenu.
            - To add contextual menu support to an entire subclass of Tkinter objects,
              do not specify wdg (or set it to None). Or use CtxMenuMixin.
        - helpURL: a URL for extensive help.
        - configFunc: the function to add items to the contextual menu;
            the function takes one argument: the menu;
            if omitted then self.ctxConfigMenu is used
        - doTest: while initializing, create a menu to make sure it works
        
        Help:
        There are multiple ways to support help for a widget. Any of these
        will cause a Help item to be added as the last item of the contextual menu
        that "does the right thing":
        - specify helpURL
        - override getHelpURL to return the desired info
            
        Error conditions:
        - Raises TypeError if wdg is already a CtxMenu object
        
        Subtleties:
        - To avoid a circular reference to self (e.g. self.__wdg = self),
          I use __getWdg to return wdg or self as appropriate.
          This may help garbage collection.
        - CtxMenu does not create a contextual menu until there is something
          to put in the menu.
        """
        self.__wdg = wdg
            
        self.helpURL = helpURL
        self.ctxSetConfigFunc(configFunc)

        self.__getWdg().bind("<<CtxMenu>>", self.__postMenu)
        
        if doTest:
            self.ctxGetMenu()
        
    def __getWdg(self):
        """Returns the widget, if specified, else self.
        """
        return self.__wdg or self

    def __postMenu(self, evt):
        """Posts the contextual menu"""
        menu = self.ctxGetMenu()
        if menu.index("end") != None:
            menu.tk_popup(evt.x_root, evt.y_root)
    
    def ctxConfigMenu(self, menu):
        """Adds all items to the contextual menu.
        Override to add your own items.
        Return True if you want a Help entry added at the bottom
        (if getHelpURL returns anything).
        """
        return True
    
    def ctxGetMenu(self):
        """Creates the contextual menu and adds items.
        Override to build your own menu from scratch.
        If you only want to add some entries, override ctxConfigMenu instead.
        """
        menu = Tkinter.Menu(master=self.__getWdg(), tearoff=0)
        if self.__configMenuFunc(menu):
            helpURL = self.getHelpURL()
            if helpURL:
                menu.add_command(label = "Help", command = self.ctxShowHelp)
        return menu
    
    def ctxSetConfigFunc(self, configFunc=None):
        """Sets the function that configures the contextual menu
        (i.e. adds items to it).
        If None, then self.ctxConfigMenu is used.
        
        The function must take one argument: the menu.

        Raise ValueError if configFunc not callable.
        """
        if configFunc and not callable(configFunc):
            raise ValueError("configFunc %r is not callable" % (configFunc,))
        self.__configMenuFunc = configFunc or self.ctxConfigMenu
    
    def ctxShowHelp(self):
        """Displays the help.
        """
        helpURL = self.getHelpURL()
        if not helpURL:
            return

        RO.Comm.BrowseURL.browseURL(helpURL)

    def getHelpURL(self):
        """Returns the instance variable helpURL.
        Override this if you want to use a help URL
        but not the default value of the combination
        of _HelpURLBase and self.helpURL.
        """
        if self.helpURL:
            return RO.Constants._joinHelpURL(self.helpURL)
        return None

class CtxMenuMixin(CtxMenu):
    """To create a new Tkinter-based widget class that intrinsically has contextual
    menu support:
    - Inherit both from a Tkinter class and from CtxMenuMixin
    - Call CtxMenuMixin.__init__(self) from your object's __init__ method (as usual)
    - If you want a help menu item, either specify helpURL in the call to __init__
      or else supply a getHelp() method that returns a help string.
    """
    def __init__(self,
        helpURL = None,
        configFunc = None,
        doTest = True,
    ):
        CtxMenu.__init__(self,
            helpURL = helpURL,
            configFunc = configFunc,
            doTest = doTest,
        )


def addCtxMenu(
    wdg,
    helpURL = None,
    configFunc = None,
    doTest = True,
):
    """Creates a CtxMenu object for your widget and adds a reference to it
    as wdg.__ctxMenu, thus saving you from having to explicitly save a reference.
    Also returns the CtxMenu item in case you want to add other menu items.
    
    Caution: do not call this on objects that already inherit from CtxMenuMixin!
    """
    wdg.__ctxMenu = CtxMenu(
        wdg=wdg,
        helpURL = helpURL,
        configFunc = configFunc,
        doTest = doTest,
    )
    return wdg.__ctxMenu


if __name__ == "__main__":
    import Bindings
    import PythonTk
    root = PythonTk.PythonTk()

    # set up standard binding for <<CtxMenu>>   
    Bindings.stdBindings(root)

    # add help to a standard Tkinter widget
    stdLabel = Tkinter.Label(text="Standard label")
    addCtxMenu(
        wdg = stdLabel,
        helpURL = "http://brokenURL.html",
    )
    stdLabel.pack()
    
    # create a new label class that automatically has help:
    class HelpLabel(Tkinter.Label, CtxMenuMixin):
        def __init__(self, master, helpURL=None, **kargs):
            Tkinter.Label.__init__(self, master=master, **kargs)
            CtxMenuMixin.__init__(self, helpURL)

    hLabel = HelpLabel(root,
        text = "Special label",
        helpURL = "http://brokenURL.html",
    )
    hLabel.pack()
    
    root.mainloop()
