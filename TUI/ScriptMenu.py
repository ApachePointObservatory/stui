#!/usr/bin/env python
"""Creates the Script menu.

To Do:
- add html help; note that this will have to be fed to ScriptWdg,
  RO.ScriptWdg has no idea of TUI help

History:
2004-07-19 ROwen
2004-08-11 ROwen    Modified for updated RO.Wdg.Toplevel.
2004-08-23 ROwen    Added some diagnostic print statements (commented out).
2004-10-11 ROwen    Modified to reject files whose names begin with ".".
2004-10-28 ROwen    Bug fix: Open... was broken.
2005-09-22 ROwen    Fix PR 272: standard scripts not available on Mac;
                    this was broken by the packaging overhaul for TUI 1.0.1.
                    Fix PR 132: Script menu may not load at first on MacOS X;
                    this was fixed via a hideous hack.
                    Modified to check/rebuild the entire menu when the root
                    menu is shown, instead of using lazy check/rebuild;
                    this simplified the hack for PR 132.
                    Modified to prebuild the menu at startup.
                    Modified test code to show a standard pull-down menu.
                    
"""
import os
import sys
import Tkinter
import tkFileDialog
import tkMessageBox
import RO.Alg
import RO.OS
import RO.Wdg
import TUI.TUIPaths
import TUI.TUIModel


def getScriptMenu(master):
    # look for TUIAddition script dirs
    addPathList = TUI.TUIPaths.getAddPaths()
    addScriptDirs = [os.path.join(path, "Scripts") for path in addPathList]
    addScriptDirs = [path for path in addScriptDirs if os.path.isdir(path)]

    # prepend the standard script dir and remove duplicates
    stdScriptDir = TUI.TUIPaths.getResourceDir("Scripts")
    scriptDirs = [stdScriptDir] + addScriptDirs
    scriptDirs = RO.OS.removeDupPaths(scriptDirs)
    
    rootNode = _RootNode(master, "", scriptDirs)
    rootNode.checkMenu(recurse=True)
    
    return rootNode.menu

class _MenuNode:
    def __init__(self, parentNode, label, pathList):
#       print "_MenuNode(%r, %r, %r)" % (parentNode, label, pathList)
        self.parentNode = parentNode
        self.label = label
        self.pathList = pathList

        self.itemDict = {}
        self.subDict = RO.Alg.ListDict()
        self.subNodeList = []

        self._setMenu()
    
    def _setMenu(self):
        self.menu = Tkinter.Menu(
            self.parentNode.menu,
            tearoff = False,
#           postcommand = self.checkMenu,
        )
        self.parentNode.menu.add_cascade(
            label = self.label,
            menu = self.menu,
        )
    
    def checkMenu(self, recurse=True):
        """Check contents of menu and rebuild if anything has changed.
        Return True if anything rebuilt.
        """
#       print "%s checkMenu" % (self,)
        newItemDict = {}
        newSubDict = RO.Alg.ListDict()
        didRebuild = False
        
        for path in self.pathList:
            for baseName in os.listdir(path):
                # reject files that would be invisible on unix
                if baseName.startswith("."):
                    continue
        
                baseBody, baseExt = os.path.splitext(baseName)
        
                fullPath = os.path.normpath(os.path.join(path, baseName))
                
                if os.path.isfile(fullPath) and baseExt.lower() == ".py":
#                   print "checkMenu newItem[%r] = %r" % (baseBody, fullPath)
                    newItemDict[baseBody] = fullPath
                
                elif os.path.isdir(fullPath) and baseExt.lower() != ".py":
#                   print "checkMenu newSubDir[%r] = %r" % (baseBody, fullPath)
                    newSubDict[baseName] = fullPath
                
#               else:
#                   print "checkMenu ignoring %r = %r" % (baseName, fullPath)
        
        if (self.itemDict != newItemDict) or (self.subDict != newSubDict):
            didRebuild = True
            # rebuild contents
#           print "checkMenu rebuild contents"
            self.itemDict = newItemDict
            self.subDict = newSubDict
            self.menu.delete(0, "end")
            self.subNodeList = []
            self._fillMenu()
#       else:
#           print "checkMenu do not rebuild contents"

        if recurse:
            for subNode in self.subNodeList:
                subRebuilt = subNode.checkMenu(recurse=True)
                didRebuild = didRebuild or subRebuilt

        return didRebuild
    
    def _fillMenu(self):
        """Fill the menu.
        """
#       print "%s _fillMenu"
        
        itemKeys = self.itemDict.keys()
        itemKeys.sort()
#       print "%s found items: %s" % (self, itemKeys)
        for label in itemKeys:
            fullPath = self.itemDict[label]
#               print "adding script %r: %r" % (label, fullPath)
            self.menu.add_command(
                label = label,
                command = _LoadScript(self, label, fullPath),
            )
        
        subdirList = self.subDict.keys()
        subdirList.sort()
#       print "%s found subdirs: %s" % (self, subdirList)
        for subdir in subdirList:
            pathList = self.subDict[subdir]
#               print "adding submenu %r: %r" % (subdir, pathList)
            self.subNodeList.append(_MenuNode(self, subdir, pathList))
    
    def getLabels(self):
        """Return a list of labels all the way up to, but not including, the root node.
        """
        retVal = self.parentNode.getLabels()
        retVal.append(self.label)
        return retVal

    def __str__(self):
        return "%s %s" % (self.__class__.__name__, ":".join(self.getLabels()))
                


class _RootNode(_MenuNode):
    def __init__(self, master, label, pathList):
        self.master = master
        _MenuNode.__init__(self, None, label, pathList)
        self.isAqua = (RO.TkUtil.getWindowingSystem() == RO.TkUtil.WSysAqua)
        
    def _setMenu(self):
        self.menu = Tkinter.Menu(
            self.master,
            tearoff = False,
            postcommand = self.checkMenu,
        )
    
    def _fillMenu(self):
        """Fill the menu.
        """
        self.menu.add_command(label="Open...", command=self.doOpen)
        _MenuNode._fillMenu(self)

    def _macRebuild(self):
        """Ugly Mac hack that somehow re-enables submenus.
        Call after changing any submenus.
        """
        #print "_macRebuild"
        tl = Tkinter.Toplevel(width=1, height=1)
        tl.update_idletasks()
        tl.destroy()
    
    def checkMenu(self, recurse=True):
        didRebuild = _MenuNode.checkMenu(self, recurse=recurse)
        if didRebuild and self.isAqua:
            self._macRebuild()
    
    def doOpen(self):
        """Handle Open... menu item.
        """
        initialDir = os.path.expanduser("~")
        if initialDir == "~":
            initialDir = None
        fullPath = tkFileDialog.askopenfilename(
            master = self.master,
            initialdir = initialDir,
            title="TUI Script",
            filetypes = [("Python", "*.py")],
        )
        if not fullPath:
            return
        _LoadScript(self, fullPath, fullPath)()

    def getLabels(self):
        """Return a list of labels all the way up to, but not including, the root node.
        """
        return []


class _LoadScript:
    def __init__(self, node, label, fullPath):
        labelSet = node.getLabels() + [label]
        self.tlName = 'ScriptNone.' + ":".join(labelSet)
#       print "_LoadScript(%s, %s, %s); tlName=%s" % (node, label, fullPath, self.tlName)
        self.fullPath = fullPath
        self.tuiModel = TUI.TUIModel.Model()
    
    def __call__(self):
        """If the script window exists, bring it to the front.
        Otherwise, load the script file into a new script window.
        """
#       print "_LoadScript.doMenu(); tlName=%s" % (tlName,)
        tl = self.tuiModel.tlSet.getToplevel(self.tlName)
        if tl:
            tl.makeVisible()
        else:
            try:
                self.tuiModel.tlSet.createToplevel(
                    name = self.tlName,
                    resizable = False,
                    wdgFunc = self.makeWdg,
                )
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                tkMessageBox.showerror(
                    message = "Could not load script:\n%r\n%s\n(See console for more info.)" % (self.fullPath, e),
                )

    def makeWdg(self, master):
#       print "_LoadScript.makeWdg(%r); tlName=%s" % (master, tlName,)
        return RO.Wdg.ScriptFileWdg(
            master=master,
            filename = self.fullPath,
            dispatcher = self.tuiModel.dispatcher,
        )


if __name__ == "__main__":
    import RO.TkUtil
    root = Tkinter.Tk()
    
    newTl = RO.Wdg.Toplevel(root, title="Other")

    menuBar = Tkinter.Menu(root)
    root["menu"] = menuBar

    scriptMenu = getScriptMenu(menuBar)
    menuBar.add_cascade(label="Scripts", menu=scriptMenu)
    
    root.mainloop()
