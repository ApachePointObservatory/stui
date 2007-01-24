#!/usr/bin/env python
"""A menu showing a history of recent events.
Saves arbitrary data associated with each event
and calls a user-specified callback when any item is selected.

History:
2002-07-31 ROwen
2002-11-26 ROwen    Added help and contextual menu support.
2002-12-04 ROwen    Swapped helpURL and helpText args.
2002-12-20 ROwen    Removed kargs from HistoryMenu.__init__; it wasn't being used;
                    thanks to pychecker.
2003-04-15 ROwen    Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-12-05 ROwen    Renamed callback to callFunc for consistency.
2004-05-18 ROwen    Stopped importing sys since it was not being used.
2004-08-11 ROwen    Define __all__ to restrict import.
2004-09-14 ROwen    Test code no longer imports RO.Wdg to avoid circular import.
"""
__all__ = ['HistoryMenu']

import Tkinter
import RO.Alg
import CtxMenu

class HistoryMenu (Tkinter.Menubutton, CtxMenu.CtxMenuMixin):
    """A menu showing a history of recent events.
    
    Inputs:
    - callFunc  function to call when a menu item is selected;
                    takes two inputs:
                    - name  the label of the menu item
                    - data  data associated with the menu item
    - removeAdjDup  removes the most recent entry, if it is a duplicate?
    - removeAllDup  removes all older duplicate entries?
    - maxEntries    the maximum number of entries;
                    older entries are purged
    
    Note: detection of duplicate entries is based on the entry name.
    The assumption is items that have different behaviors
    should also have different names.
    """
    def __init__(self,
        master,
        callFunc,
        removeAdjDup = 0,
        removeAllDup = 0,
        maxEntries = 30,
        helpText = None,
        helpURL = None,
    ):
        Tkinter.Menubutton.__init__(self,
            master=master,
            text="History",
            indicatoron=1,
            relief="raised",
#           state="disabled",
        )
        CtxMenu.CtxMenuMixin.__init__(self, helpURL = helpURL)

        self.__callFunc = callFunc
        self.__removeAdjDup = removeAdjDup
        self.__removeAllDup = removeAllDup
        self.__maxEntries = maxEntries
        self.helpText = helpText

        # basic menu
        self.__menu = Tkinter.Menu(self, tearoff=0)
        self["menu"] = self.__menu
    
        self.dataDict = {}
    
    def addItem(self, name, data):
        """Adds a new entry at the top of the history menu.
        
        Inputs:
        - name  label for the new menu item
        - data  data associated with this menu item
        
        If this menu item is selected, the callback function
        is called with arguments: name, data.
        """
        # remove duplicates as configured
        # count down from the end to avoid changing the index
        # of items that have not yet been tested
        startInd = self.nItems() - 1
        if self.__removeAllDup:
            endInd = -1
        elif self.__removeAdjDup:
            endInd = max(-1, startInd-1)
        else:
            endInd = startInd
        for ind in range(startInd, endInd, -1):
            if name == self.__menu.entrycget(ind, "label"):
                self.__menu.delete(ind)

        # if menu will be too long after adding the new item, shorten it
        if self.nItems() >= self.__maxEntries:
            self.__menu.delete("end")

        # insert the new item at the beginning (top) of the menu
        self.__menu.insert_command (
            0,
            label = name,
            command = RO.Alg.GenericCallback(self.__callFunc, name, data),
        )
#       self["state"] = "normal"
    
    def nItems(self):
        """Returns the number of items in the history menu.
        """
        lastIndex = self.__menu.index("end")
        if lastIndex == None:
            return 0
        return lastIndex + 1
        

if __name__ == "__main__":
    import PythonTk
    root = PythonTk.PythonTk()
    
    def doAdd(*args):
        name = nameVar.get()
        testFrame.addItem(name, "data for %s" % name)
        nameVar.set("")
        
    def doPrint(name, data):
        print "name=%r, data=%r" % (name, data)
    
    Tkinter.Label(root, text="Name of new entry (type <CR> to accept it):").pack()
    nameVar = Tkinter.StringVar()
    nameWdg = Tkinter.Entry(root, textvariable=nameVar)
    nameWdg.bind("<Return>", doAdd)
    nameWdg.pack()
    testFrame = HistoryMenu(root,
        callFunc=doPrint,
        removeAllDup=1,
        maxEntries=5,
        helpText = "sample history menu; enter data above and type return to enter it in the history menu",
    )
    testFrame.pack()
    
    testFrame.addItem("first item", {1:1, 2:3})
    testFrame.addItem("second item", "hello")
    
    root.mainloop()
