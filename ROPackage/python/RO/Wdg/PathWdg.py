#!/usr/bin/env python
"""Widgets for selecting files and directories.

To do:
- If the user clicks to select a new dir or file and the current
one is missing, this could be handled a bit better:
- presently if the user cancels, the current value is left alone
  even though it is now known to be invalid. It should probably be
  cleared instead.

History:
2006-03-07 ROwen
2006-04-27 ROwen    FileWdg and DirWdg ignored maxChar (thanks pychecker!).
2006-06-05 ROwen    If the current path is missing when the user selects a new one,
                    the dialog box starts at the parent dir (if found).
                    Bug fix: if the current path was missing, the choose dialog would not come up.
                    Bug fix: FileWdg does not set defPath or path if defPath is a directory
                    (but it still uses the value as the initial directory of the choose dialog).
                    Moved more functionality to BasePathWdg.
2006-06-08 ROwen    FilePathWdg bug fix: initial defPath not shown.
"""
import os
import tkFileDialog
import Tkinter
import RO.AddCallback
import RO.Constants
import CtxMenu
from SeverityMixin import SeverityActiveMixin

__all__ = ["DirWdg", "FileWdg"]

class BasePathWdg (Tkinter.Button, RO.AddCallback.BaseMixin, CtxMenu.CtxMenuMixin,
    SeverityActiveMixin):
    def __init__(self,
        master,
        defPath = None,
        fileTypes = None,
        maxChar = 30,
        callFunc = None,
        severity = RO.Constants.sevNormal,
        helpText = None,
        helpURL = None,
    **kargs):
        """Creates a new Button.
        
        Inputs:
        - defPath: initial path; silently ignored if invalid or nonexistent
        - fileTypes: sequence of (label, pattern) tuples;
            use * as a pattern to allow all files of that labelled type;
            omit altogether to allow all files
        - maxChar: maximum # of characters of file path to display
        - callFunc  callback function; the function receives one argument: self.
                    It is called whenever the value changes (manually or via
                    the associated variable being set).
        - severity  initial severity; one of RO.Constants.sevNormal, sevWarning or sevError
        - helpText  text for hot help
        - helpURL   URL for longer help
        - all remaining keyword arguments are used to configure the Tkinter Button;
          command is supported, for the sake of conformity, but callFunc is preferred.
        """
        self.fileTypes = fileTypes
        self.maxChar = max(3, int(maxChar))
        self.helpText = helpText
        self.path = None
        self.defPath = None
        
        self.leftChar = 0
        self.rightChar = (self.maxChar - self.leftChar) - 1

        Tkinter.Button.__init__(self,
            master = master,
            command = self._doChoose,
        **kargs)
        
        RO.AddCallback.BaseMixin.__init__(self)
        
        CtxMenu.CtxMenuMixin.__init__(self,
            helpURL = helpURL,
        )
        SeverityActiveMixin.__init__(self, severity)

        self._initPath(defPath)
        
        if callFunc:
            self.addCallback(callFunc, False)

    def _doChoose(self):
        """Put up a dialog to choose a new file.
        Subclasses must override.
        """
        raise NotImplementedError("_doChoose must be implemented by a subclass")

    def _initPath(self, defPath):
        """During initialization set self.defPath and self.path.
        """
        #print "%s._initPath(%r)" % (self.__class__.__name__, defPath)
        if defPath != None:
            try:
                self.checkPath(defPath)
                defPath = os.path.abspath(defPath)
            except ValueError:
                #print "%s._initPath: path invalid"
                defPath = None
        self.defPath = defPath
        self.setPath(defPath)
    
    def checkPath(self, path):
        """Raise ValueError if path not None and does not exist.
        Override from base class to make more specific.
        """
        if path != None and not os.path.exists(path):
            raise ValueError("Path %r does not exist" % (path,))
    
    def setEnable(self, doEnable):
        if doEnable:
            self["state"] = "normal"
        else:
            self["state"] = "disabled"
    
    def getEnable(self):
        return self["state"] == "normal"
        
    def setPath(self, path):
        """Set self.path to normalized version of path.
        path may be None.
        
        Raise ValueError if path invalid or nonexistent.
        """
        #print "%s.setPath(%r)" % (self.__class__.__name__, path)
        if path == None:
            dispStr = ""
        else:
            self.checkPath(path)
            path = os.path.abspath(path)
            if len(path) > self.maxChar:
                dispStr = "".join((
                    path[0:self.leftChar],
                    u"\N{HORIZONTAL ELLIPSIS}",
                    path[-self.rightChar:],
                ))
            else:
                dispStr = path
        self.path = path
        self["text"] = dispStr
        self._doCallbacks()
    
    def getPath(self):
        """Return the current path (or None if no path).
        """
        #print "%s.getPath() = %r" % (self.__class__.__name__, self.path)
        return self.path

    def ctxConfigMenu(self, menu):
        """Configure the contextual menu.
        Called just before the menu is posted.
        """
        if not self.getEnable():
            return True
        
        if self.path == None:
            state = "disabled"
        else:
            state = "normal"
        
        if self.path:
            copyLabel = " ".join(("Copy", self.path))
        else:
            copyLabel = "Copy"
        menu.add_command(
            label = copyLabel,
            command = self._copyToClip,
            state = state,
        )
        return True
    
    def _copyToClip(self):
        """Copy the current path to the clipboard
        """
        if self.path != None:
            self.clipboard_clear()
            self.clipboard_append(self.path)

class DirWdg(BasePathWdg):
    """A widget showing a directory; push to pick another directory.
    
    Inputs: same as BasePathWdg. defPath must be a an existing directory,
    else it is silently ignored.
    """
    def _doChoose(self):
        """Put up a dialog to choose a new file.
        """
        if self.path != None:
            startDir = self.path
        else:
            startDir = self.defPath

        # if path missing, try parent directory
        # and if that's gone, give up on startDir
        if not os.path.isdir(startDir):
            parDir = os.path.split(self.path)[0]
            if os.path.isdir(parDir):
                startDir = parDir
            else:
                startDir = None
            
        kargs = {}
        if self.fileTypes:
            kargs["filetypes"] = self.fileTypes
        newPath = tkFileDialog.askdirectory(
            initialdir = startDir,
            mustexist = True,
            title = self.helpText,
        **kargs)
        if newPath:
            # handle case of newPath being a weird Tcl object
            newPath = RO.CnvUtil.asStr(newPath)
            self.setPath(newPath)
    
    def checkPath(self, path):
        """Raise ValueError if path not None and not an existing directory"""
        if path != None and not os.path.isdir(path):
            raise ValueError("Path %r is not an existing directory" % (path,))
        
    
            
class FileWdg(BasePathWdg):
    """A widget showing a file; push to pick another file.
    
    Inputs: same as BasePathWdg. defPath may be an existing file or a directory;
    if a directory, it is only used as the initial directory of the chooser dialog.
    """
    def _doChoose(self):
        """Put up a dialog to choose a new file.
        """
        if self.path != None:
            startPath = self.path
        else:
            startPath = self.defPath
        
        if startPath != None:
            startDir, startFile = os.path.split(self.path)
            if not os.path.isfile(startPath):
                startFile = None
        else:
            startFile = None
            startDir = self.defDir

        if startDir != None and not os.path.isdir(startDir):
            startDir = startFile = None

        kargs = {}
        if self.fileTypes:
            kargs["filetypes"] = self.fileTypes
        newPath = tkFileDialog.askopenfilename(
            initialdir = startDir,
            initialfile = startFile,
            title = self.helpText,
        **kargs)
        if newPath:
            # handle case of newPath being a weird Tcl object
            newPath = RO.CnvUtil.asStr(newPath)
            self.setPath(newPath)
    
    def _initPath(self, defPath):
        """During initialization set self.defDir, self.defPath and self.path.
        """
        defDir = None
        if defPath != None:
            if os.path.isfile(defPath):
                defPath = os.path.abspath(defPath)
            elif os.path.isdir(defPath):
                defDir = os.path.abspath(defPath)
                defPath = None
            else:
                # if parent dir exists, use that; else all None
                parDir = os.path.split(defPath)[0]
                if os.path.isdir(parDir):
                    defDir = parDir
                defPath = None
        self.defDir = defDir
        self.defPath = defPath
        self.setPath(defPath)

    def checkPath(self, path):
        """Raise ValueError if path not None and not not an existing file"""
        if path != None and not os.path.isfile(path):
            raise ValueError("Path %r is not an existing file" % (path,))


if __name__ == "__main__":
    from RO.Wdg.PythonTk import PythonTk
    root = PythonTk()
    
    modFile = __file__
    modDir = os.path.split(__file__)[0]
    
    def wdgFunc(wdg):
        print "%s set to %s" % (wdg.__class__.__name__, wdg.getPath())

    f1 = FileWdg(root, callFunc=wdgFunc)
    f1.pack()
    
    f2 = FileWdg(root, callFunc=wdgFunc, defPath=modDir)
    f2.pack()
    
    f3 = FileWdg(root, callFunc=wdgFunc, defPath=modFile)
    f3.pack()

    d1 = DirWdg(root, callFunc=wdgFunc)
    d1.pack()
    
    d2 = DirWdg(root, callFunc=wdgFunc, defPath=modDir)
    d2.pack()
    
    root.mainloop()
