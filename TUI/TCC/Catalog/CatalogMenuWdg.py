#!/usr/bin/env python
"""Widget that displays a catalog pop-up menu.

Note: catalogs are stored by catalog file "base name",
i.e. the file name without any path information.
If you have a catalog open with a given name
and try to open another with the same name,
the information from the first is no longer displayed.

History:
2003-10-30 ROwen
2004-03-08 ROwen    Modified to support multiple catalogs and large catalogs.
                    Converts return from tkFileDialog to string, "just in case".
2004-03-11 ROwen    Bug fix: was calling callFunc with the wrong object.
2004-05-18 ROwen    Stopped importing tkMessageBox; it wasn't used.
                    Eliminated a redundant import in the test code.
2004-08-11 ROwen    Modified for updated RO.Wdg.CtxMenu.
2004-09-07 ROwen    Open... dialog remembers most recent directory.
                    Open... dialog no longer shows invisible files
                    by default on X11 (never an issue on Aqua or Win).
2004-10-12 ROwen    Bug fix: if the catalog parser gave up, no error message
                    was printed and "Loading..." was shown indefinitely.
                    Also, if statusBar omitted, messages are printed to stderr.
2005-01-05 ROwen    Changed level to severity.
"""
import os
import sys
import Tkinter
import tkFileDialog
import RO.Constants
import RO.CnvUtil
import RO.StringUtil
import RO.Alg
import RO.TkUtil
import RO.Wdg
import TUI.Base.Wdg
import TUI.TCC.UserModel
import ParseCat

_NItems = 20    # number of items in partial menu
_MaxItems = 25  # max # of items in a menu

class CatalogMenuWdg(Tkinter.Frame):
    """Display a catalog pop-up menu.
    
    Inputs:
    - master: master widget
    - callFunc: a function that is called when a catalog entry is selected;
        it receives one argument: the selected TUI.TCC.TelTarget object
    - helpText:
    - helpURL: 
    - statusBar: TUI.Base.Wdg.StatusBar in which to display catalog loading status
    """
    def __init__(self,
        master,
        callFunc = None,
        helpText = None,
        helpURL = None,
        statusBar = None,
    ):
        Tkinter.Frame.__init__(self, master)
        self.callFunc = callFunc
        self._catParser = ParseCat.CatalogParser()
        userModel = TUI.TCC.UserModel.Model()
        self.userCatDict = userModel.userCatDict
        self.statusBar = statusBar
        
        # create file dialog (reusing the same one
        # means the directory is the same each time)
        initialDir = os.path.expanduser("~")
        if initialDir == "~":
            initialDir = None
        
        if RO.TkUtil.getWindowingSystem() == RO.TkUtil.WSysX11:
            filetypes = [("Visible", "{[a-zA-Z0-9_]*}"), ("All", "*")]
        else:
            filetypes = []
        self.fileDialog = tkFileDialog.Open(
            parent = self,
            initialdir = initialDir,
            filetypes = filetypes,
            title = "Catalog File",
        )
        
        # build the menu button and menu
        self.menuButton = Tkinter.Menubutton(
            master = self,
            text = "Catalog",
            borderwidth = 2,
            indicatoron = True,
            relief = "raised",
            anchor = "c",
            highlightthickness = 2,
        )
        self.menu = Tkinter.Menu(
            master = self.menuButton,
            tearoff = False,
        )
        self._buildMenu()
        self.menuButton["menu"] = self.menu
        self.menuButton.pack()
        
        # handle help
        RO.Wdg.addCtxMenu(
            wdg = self.menuButton,
            helpURL = helpURL,
        )
        self.helpText = helpText
        
        # set callback so menu is updated when catalog changes
        self.userCatDict.addCallback(self._updUserCatDict)

    def _doClose(self, catName):
        """Remove all info associated with the specified catalog file.
        catName is the catalog file name with no path info.
        """
#       print "_doClose(%r)" % (catName,)
        catDict = self.userCatDict.get()
        if catName in catDict:
            del catDict[catName]
            self.userCatDict.set(catDict)
    
    def _doMenu(self, obj):
#       print "_doMenu(%r)" % (obj,)
        if self.callFunc:
            self.callFunc(obj)          
    
    def _doOpen(self):
        """Open a new catalog.
        """
        initialDir = os.path.expanduser("~")
        if initialDir == "~":
            initialDir = None
        catFile = self.fileDialog.show()
        if not catFile:
            return
        # in case a Tcl object was returned...
        catFile = RO.CnvUtil.asStr(catFile)
        
        # parse the catalog file
        # print "loading catalog %r" % (catFile,)
        self.showMsg("Loading file %s" % (catFile,))
        self.update_idletasks()
        try:
            objCat, errList = self._catParser.parseCat(catFile)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            self.showMsg(
                msgStr = "Could not load %s: %s" % (catFile, e),
                severity = RO.Constants.sevError,
            )
            return
        
        catName = objCat.name
        
        # report errors, if any
        if errList:
            _CatalogErrBox(self, catFile, errList)
        
        # update userCatDict in userModel
        # (automatically triggers menu rebuild)
        catDict = self.userCatDict.get()
        catDict[catName] = objCat
        self.userCatDict.set(catDict)

        # indicate completion
        self.showMsg("Catalog %s loaded" % (catName,))

    def _addCatMenu(self, objCat):
        """Add the menu(s) for a given catalog to the main menu.
        """
        catName = objCat.name
        objList = objCat.objList
        
        # create new menu(s)
        begInd = 0
        nRemain = len(objList)
        justOneMenu = True
        while begInd < len(objList):
            nRemain = len(objList) - begInd
            if nRemain > _MaxItems:
                nPick = _NItems
                justOneMenu = False
            else:
                nPick = nRemain
            endInd = begInd + nPick

            # create submenu for items begInd:endInd
            menu = Tkinter.Menu(
                master = self.menu,
                tearoff = False,
            )
            for obj in objList[begInd:endInd]:
                item = str(obj)
                menu.add_command(
                    label = item,
                    command = RO.Alg.GenericCallback(self._doMenu, obj),
                )
                
            menu.add_separator()
            
            menu.add_command(
                label = "Close",
                command = RO.Alg.GenericCallback(self._doClose, catName),
            )
            
            # add entry to main menu
            if justOneMenu:
                entryName = catName
            else:
                entryName = "%s (%s-%s)" % (catName, begInd+1, endInd)
            
            self.menu.add_cascade(
                label = entryName,
                menu = menu,
            )
            
            begInd = endInd
    
    def _buildMenu(self):
        """Build or rebuild the entire menu.
        """
        # empty the current menu
        self.menu.delete(0, "end")      

        # add Open...
        self.menu.add_command(
            label = "Open...",
            command = self._doOpen,
        )
        
        catDict = self.userCatDict.get()
        if not catDict:
            return
        
        catNames = catDict.keys()
        catNames.sort()
        for catName in catNames:
            self._addCatMenu(catDict[catName])
    
    def _updUserCatDict(self, userCatDict=None):
        """UserCatDict updated; update the menu accordingly.
        """
        self._buildMenu()
    
    def showMsg(self, msgStr, severity=RO.Constants.sevNormal):
        if self.statusBar:
            self.statusBar.setMsg(
                msgStr = msgStr,
                severity = severity,
            )
        else:
            sys.stderr.write(msgStr + "\n")


class _CatalogErrBox(Tkinter.Toplevel):
    def __init__(self,
        master,
        catFile,
        errList,
    ):
        Tkinter.Toplevel.__init__(self, master)
        self.title("Catalog Errors")
        self.geometry("+%d+%d" % (master.winfo_rootx()+50,
            master.winfo_rooty()+50))

        self.yscroll = Tkinter.Scrollbar (
            master = self,
            orient = "vertical",
        )
        self.text = Tkinter.Text (
            master = self,
            yscrollcommand = self.yscroll.set,
            wrap = "word",
            width = 50,
            height = 10,
        )
        self.yscroll.configure(command=self.text.yview)
        self.yscroll.grid(row=0, column=1, sticky="ns")
        self.text.grid(row=0, column=0, sticky="nsew")
        RO.Wdg.makeReadOnly(self.text)

        self.okBut = Tkinter.Button(self,
            text = "OK",
            command = self.ok,
            default = "active",
        )
        self.okBut.grid(row=1, column=0, columnspan=2)
        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.bind("<KeyPress-Return>", self.ok)
        
        nErrors = len(errList)
        self.addStr("%d %s rejected from catalog:\n%s\n\n" % (
                nErrors,
                RO.StringUtil.plural(nErrors, "object was", "objects were"),
                catFile,
            )
        )
        
        for badLine, errMsg in errList:
            self.addStr("%s\n   error: %s\n" % (badLine, errMsg))
    
    def addStr(self, astr):
        self.text.insert("end", astr)
    
    def ok(self, *args):
        self.destroy()

if __name__ == "__main__":
    import TUI.Models.TUIModel

    root = RO.Wdg.PythonTk()
    root.resizable(width=0, height=0)
    
    tuiModel = TUI.Models.TUIModel.Model(True)
    
    def printObj(obj):
        print obj

    testFrame = CatalogMenuWdg(master=root, callFunc=printObj)
    testFrame.pack()

    root.mainloop()
