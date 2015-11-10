#!/usr/bin/env python
"""An object that loads a script given its path

History:
2014-02-11 ROwen    Extracted from TUI.ScriptMenu and renamed from _LoadScript
2015-11-05 ROwen    Ditched obsolete "except (SystemExit, KeyboardInterrupt): raise" code
"""
import os
import tkMessageBox
import RO.Constants
import RO.OS
from RO.StringUtil import strFromException
import TUI.Base.Wdg
import TUI.TUIPaths
import TUI.Models

__all__ = ("getScriptDirs", "ScriptLoader", "reopenScriptWindows", "ScriptWindowNamePrefix")

ScriptWindowNamePrefix = "ScriptNone"

def getScriptDirs():
    """Return script directories

    Return order is:
    - built-in
    - local TUIAdditions/Scripts
    - shared TUIAdditions/Scripts
    """
    # look for TUIAddition script dirs
    addPathList = TUI.TUIPaths.getAddPaths()
    addScriptDirs = [os.path.join(path, "Scripts") for path in addPathList]
    addScriptDirs = [path for path in addScriptDirs if os.path.isdir(path)]

    # prepend the standard script dir and remove duplicates
    stdScriptDir = TUI.TUIPaths.getResourceDir("Scripts")
    scriptDirs = [stdScriptDir] + addScriptDirs
    scriptDirs = RO.OS.removeDupPaths(scriptDirs)
    return scriptDirs


class ScriptLoader:
    """An object that will load a specific script when called
    """
    def __init__(self, subPathList, fullPath, showErrDialog=True):
        """Construct a ScriptLoader

        Inputs:
        - subPathList: list of path elements relative to TUIAdditions/Scripts
        - fullPath: full path to script file
        """
        self.tlName = "%s.%s" % (ScriptWindowNamePrefix, ":".join(subPathList))
#       print "ScriptLoader(subPathList=%r, fullPath=%r); tlName=%s" % (subPathList, fullPath, self.tlName)
        self.fullPath = fullPath
        self.showErrDialog = bool(showErrDialog)
        self.tuiModel = TUI.Models.getModel("tui")
    
    def __call__(self):
        """If the script window exists, bring it to the front.
        Otherwise, load the script file into a new script window.
        """
#       print "ScriptLoader.doMenu(); tlName=%s" % (tlName,)
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
            except Exception as e:
                if self.showErrDialog:
                    tkMessageBox.showerror(
                        message = "Could not load script:\n%r\n%s\n(See console for more info.)" % (self.fullPath, strFromException(e)),
                    )
                else:
                    self.tuiModel.logMsg(
                        msgStr = "Could not load script: %r: %s" % (self.fullPath, strFromException(e)),
                        severity = RO.Constants.sevWarning,
                    )

    def makeWdg(self, master):
#       print "ScriptLoader.makeWdg(%r); tlName=%s" % (master, tlName,)
        return TUI.Base.Wdg.ScriptFileWdg(
            master=master,
            filename = self.fullPath,
            dispatcher = self.tuiModel.dispatcher,
        )

def reopenScriptWindows():
    """Reopen script windows that were open before
    """
    scriptDirs = getScriptDirs()
    tuiModel = TUI.Models.getModel("tui")
    tlSet = tuiModel.tlSet
    scriptNames = tlSet.getNamesInGeomFile(prefix=ScriptWindowNamePrefix)
    for name in scriptNames:
        if tlSet.getDesVisible(name):
            # name format is <ScriptWindowNamePrefix>.<colon-separated-subPath>
            subPathList = name.split(".")[1].split(":")
            subPath = os.path.join(*subPathList) + ".py"
            for scriptDir in scriptDirs:
                fullPath = os.path.join(scriptDir, subPath)
                if os.path.isfile(fullPath):
                    ScriptLoader(subPathList=subPathList, fullPath=fullPath, showErrDialog=False)()
                    continue




