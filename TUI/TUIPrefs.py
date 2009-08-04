#!/usr/bin/env python
"""A set of preferences for TUI

To Do:
- Fix the bug that (at least on MacOS X with aqua Tk 8.4.1) the labels
    for the various prefs have their own font, which is not the main font

History:
2002-03-08 ROwen    First release
2002-11-13 ROwen    If the user has a home directory, the prefs file is stored there
2003-02-28 ROwen    Added sanity checking to username and host prefs.
2003-04-09 ROwen    Changed shortDescr to helpText, preperatory to full help implementation.
2003-04-22 ROwen    Fixed the default host.
2003-06-18 ROwen    Modified to test for StandardError instead of Exception
2003-08-07 ROwen    Bug fix: was not setting up prefs in RO.Wdg.
2003-08-11 ROwen    Added auto FTP prefs.
2003-08-25 ROwen    Re-added Misc Font lost in 2003-08 update.
2003-11-24 ROwen    Added sounds.
2003-12-03 ROwen    Added Guiding Begins, Guiding Ends, Exposure Begins, Exposure Ends.
2003-12-23 ROwen    Modified to use .wav instead of .aiff.
2004-02-03 ROwen    Modified to use RO.OS.getPrefsDir and thus to
                    look for the prefs file where it really belongs.
2004-09-09 ROwen    Added "Seq By File" preference.
2005-06-10 ROwen    Added "No Guide Star" sound preference.
2005-07-14 ROwen    Default Save As= user's documents directory.
2005-08-02 ROwen    Modified to find Sounds dir without assuming it is a package.
2005-09-15 ROwen    Renamed preference "Auto FTP" to "Auto Get".
                    Added preference "View Image".
                    Changed "get" to "download" in help text for exposures prefs.
2005-09-23 ROwen    Added anchors to help URLs for exposure and sound prefs.
2005-09-28 ROwen    Modified to use RO.OS.getPrefsDirs instead of getPrefsDir.
2005-10-06 ROwen    getprefsDir needs new inclNone=True argument.
2006-04-14 ROwen    Added "Guide Mode Changes" sound preference.
2006-05-19 ROwen    Added Guide Color prefs.
2006-10-24 ROwen    Added "Debug Color" color pref.
                    Added "Highlight Background" color pref.
                    Added "Log Highlighted Text" sound pref.
2007-09-05 ROwen    Fixed test code.
2007-11-16 ROwen    Modified to allow a port as part of Host address.
2008-07-07 ROwen    Added UMask preference.
2009-07-14 ROwen    Added Bad Pixel Color preference.
"""
#import pychecker.checker
import os
import sys
import Tkinter
import tkFont
import TUI
import RO.OS
from RO.Prefs import PrefVar
from RO.Prefs import PrefWdg
import RO.Wdg

_HelpURL = "TUIMenu/PreferencesWin.html"
_ExposuresHelpURL = _HelpURL + "#Exposures"
_SoundHelpURL = _HelpURL + "#Sounds"

def _getPrefsFile():
    prefsDir = RO.OS.getPrefsDirs(inclNone=True)[0]
    if prefsDir == None:
        raise RuntimeError("Cannot determine prefs dir")
    prefsName = RO.OS.getPrefsPrefix() + "TUIPrefs"
    return os.path.join(prefsDir, prefsName)

_SoundsDir = RO.OS.getResourceDir(TUI, "Sounds")

class TUIPrefs(PrefVar.PrefSet):
    def __init__(self,
        defFileName = _getPrefsFile(),
    ):
        # create Font objects for the various types of widgets we wish to control
        # and connect them to the widgets via the option database
        defMainFontWdg = Tkinter.Label()
        defDataFontWdg = Tkinter.Entry()
        
        # one must set umask to read it; blecch
        defUMaskInt = os.umask(0)
        os.umask(defUMaskInt)
        defUMaskStr = "%04o" % (defUMaskInt,)
        
        # set up the preference list
        prefList = (
            PrefVar.StrPrefVar(
                name = "User Name",
                category = "Connection",
                defValue = "",
                partialPattern = r"^([a-zA-Z_][-_.a-zA-Z0-9]*)?$",
                helpText = "Your name (no spaces)",
                helpURL = _HelpURL,
            ),
            PrefVar.StrPrefVar(
                name = "Host",
                category = "Connection",
                defValue = "hub25m.apo.nmsu.edu",
                helpText = "IP address of remote computer (and optional port)",
                helpURL = _HelpURL,
                partialPattern = r"^[-_.a-zA-Z0-9]*( +[0-9]*)?$",
                editWidth=24,
            ),
            
            PrefVar.BoolPrefVar(
                name = "Seq By File",
                category = "Exposures",
                defValue = False,
                helpText = "Number files by file name or by directory?",
                helpURL = _ExposuresHelpURL,
            ),
            PrefVar.BoolPrefVar(
                name = "Auto Get",
                category = "Exposures",
                defValue = False,
                helpText = "Automatically download images?",
                helpURL = _ExposuresHelpURL,
            ),
            PrefVar.BoolPrefVar(
                name = "Get Collab",
                category = "Exposures",
                defValue = True,
                helpText = "Download collaborators' images?",
                helpURL = _ExposuresHelpURL,
            ),
            PrefVar.DirectoryPrefVar(
                name = "Save To",
                category = "Exposures",
                defValue = RO.OS.getDocsDir(),
                helpText = "Directory in which to save images",
                helpURL = _ExposuresHelpURL,
            ),
            PrefVar.BoolPrefVar(
                name = "View Image",
                category = "Exposures",
                defValue = False,
                helpText = "Automatically display image?",
                helpURL = _ExposuresHelpURL,
            ),
            PrefVar.StrPrefVar(
            	name = "UMask",
            	category = "Exposures",
            	defValue = defUMaskStr,
                partialPattern = r"^[0-8]{0,4}$",
                editWidth = 5,
                callFunc = setUMask,
            	helpText = "umask for saved images and other files",
            	helpURL = _ExposuresHelpURL,
            ),

            PrefVar.FontPrefVar(
                name = "Misc Font",
                category = "Fonts",
                defWdg = defMainFontWdg,
                optionPatterns = ("*font",),
                helpText = "Font for buttons, menus, etc.",
                helpURL = _HelpURL,
            ),

            PrefVar.FontPrefVar(
                name = "Data Font",
                category = "Fonts",
                defWdg = defDataFontWdg,
                optionPatterns = ("*Entry.font", "*Text.font", "*Label.font",),
                helpText = "Font for text input and display",
                helpURL = _HelpURL,
            ),
            
            PrefVar.ColorPrefVar(
                name = "Background Color",
                category = "Colors",
                defValue = Tkinter.Label().cget("background"),
                wdgOption = "background",
                helpText = "Background color for most widgets",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Foreground Color",
                category = "Colors",
                defValue = Tkinter.Label().cget("foreground"),
                wdgOption = "foreground",
                helpText = "Color for normal text, etc.",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Debug Color",
                category = "Colors",
                defValue = "#006723",
                helpText = "Color that indicates a debug-level message",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Warning Color",
                category = "Colors",
                defValue = "blue2",
                helpText = "Color that indicates a warning",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Error Color",
                category = "Colors",
                defValue = "red",
                helpText = "Color that indicates an error",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Bad Background",
                category = "Colors",
                defValue = "pink",
                helpText = "Background color for invalid data",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Highlight Background",
                category = "Colors",
                defValue = "#bdffe0",
                helpText = "Background color for highlighted text",
                helpURL = _HelpURL,
            ),
            
            PrefVar.ColorPrefVar(
                name = "Centroid Color",
                category = "Guide Colors",
                defValue = "cyan",
                helpText = "Color for manually centroided stars",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Found Star Color",
                category = "Guide Colors",
                defValue = "green",
                helpText = "Color for automatically found stars",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Guide Star Color",
                category = "Guide Colors",
                defValue = "magenta",
                helpText = "Color for guide stars",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Boresight Color",
                category = "Guide Colors",
                defValue = "cyan",
                helpText = "Color for boresight",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Saturated Pixel Color",
                category = "Guide Colors",
                defValue = "red",
                helpText = "Color for saturated pixels",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Bad Pixel Color",
                category = "Guide Colors",
                defValue = "purple",
                helpText = "Color for bad pixels",
                helpURL = _HelpURL,
            ),
            PrefVar.ColorPrefVar(
                name = "Masked Pixel Color",
                category = "Guide Colors",
                defValue = "green",
                helpText = "Color for masked pixels",
                helpURL = _HelpURL,
            ),
            
            PrefVar.SoundPrefVar(
                name = "Axis Halt",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "AxisHalt.wav"),
                bellNum = 3,
                bellDelay = 100,
                helpText = "Sound for some axis halting",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Axis Slew",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "AxisSlew.wav"),
                bellNum = 1,
                helpText = "Sound for start of axis slew",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Axis Track",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "AxisTrack.wav"),
                bellNum = 2,
                bellDelay = 150,
                helpText = "Sound for start of axis tracking",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Command Done",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "CommandDone.wav"),
                bellNum = 1,
                helpText = "Sound for command ended successfully",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Command Failed",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "CommandFailed.wav"),
                bellNum = 3,
                bellDelay = 100,
                helpText = "Sound for command failed",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Exposure Begins",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "ExposureBegins.wav"),
                bellNum = 1,
                helpText = "Sound for start of exposure",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Exposure Ends",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "ExposureEnds.wav"),
                bellNum = 2,
                bellDelay = 100,
                helpText = "Sound for end of exposure",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Guiding Begins",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "GuidingBegins.wav"),
                bellNum = 1,
                helpText = "Sound for start of guiding",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Guide Mode Changes",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "GuideModeChanges.wav"),
                bellNum = 1,
                helpText = "Sound for a change in guide mode",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Guiding Ends",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "GuidingEnds.wav"),
                bellNum = 2,
                bellDelay = 100,
                helpText = "Sound for end of guiding",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Message Received",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "MessageReceived.wav"),
                bellNum = 1,
                helpText = "Sound for message received",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "No Guide Star",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "NoGuideStar.wav"),
                bellNum = 2,
                helpText = "Sound for guiding loop found no stars",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Log Highlighted Text",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "LogHighlightedText.wav"),
                bellNum = 2,
                helpText = "Sound when highlighted text is added to log",
                helpURL = _SoundHelpURL,
            ),
            PrefVar.SoundPrefVar(
                name = "Serious Alert",
                category = "Sounds",
                defValue = os.path.join(_SoundsDir, "SeriousAlert.wav"),
                bellNum = 3,
                helpText = "Sound for a serious or critical alert",
                helpURL = _SoundHelpURL,
            ),
        )
        PrefVar.PrefSet.__init__(self,
            prefList = prefList,
            defFileName = defFileName,
            defHeader = """Preferences for the Telescope User Interface\n""",
            oldPrefInfo = {"Auto FTP": "Auto Get"},
        )

        try:
            self.readFromFile()
        except StandardError, e:
            sys.stderr.write ("could not read TUI preferences: %s\n" % (e,))
        
        # set preferences for RO.Wdg objects
        RO.Wdg.WdgPrefs.setWdgPrefs(self)
    
    def getWdg(self, master):
        """Returns a preferences setting widget.
        """
        return PrefWdg.PrefWdg (master = master, prefSet = self)

def getFont(wdgClass, optionPattern=None):
    """Creates a Font object that is initialized to the default value of the specified
    type of widget (e.g. Tkinter.Label). optionPattern is an option database pattern;
    if supplied, an entry to the database is added for this pattern using this new Font.
    Hence the font can be connected up to automatically update a class of widgets.
    
    Not used anymore; delete once auto-update of colors is handled.
    """
    aWdg = wdgClass()
    defFontDescr = aWdg.cget("font")
    theFont = tkFont.Font(font=defFontDescr)
    if optionPattern:
        aWdg.option_add(optionPattern, theFont)
    return theFont  

def setUMask(umaskStr, prefVar=None):
	"""Handle changes to the UMask preference.
	
	Inputs:
	- umaskStr: umask value as a string of octal digits (e.g. "0022")
	- prefVar: preference variable (optional)
	"""
	umaskStr = umaskStr or "0" # convert None or "" to "0"
	os.umask(int(umaskStr, 8))

if __name__ == "__main__":
    import RO.Wdg
    root = RO.Wdg.PythonTk()

    prefs = TUIPrefs()

    testFrame = prefs.getWdg(root)
    testFrame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
    root.title("Test Preferences for TUI")

    root.mainloop()
