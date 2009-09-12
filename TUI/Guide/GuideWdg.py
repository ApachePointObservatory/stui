#!/usr/bin/env python
"""Guiding support

NEED TO FIX:
- Record all outstanding commands in a list;
  probably use a new object instead of a tuple, so the entries are named
- X will cancel ALL outstanding commands in the list
- failCmd should probably work even if cmdBtn not specified
- Need to be able to change the exposure time;
  this may involve Apply and Current or it may not;
  if it does, I think some code needs to be changed;
  the modOnly stuff is no longer needed, I believe.
  Another option is a button "ExpTime" to change the expTime;
  this is good because you can't be in the middle of changing the expTime
  and have it suddenly revert because a new image came in,
  but it is bad because then what does it mean to edit Exp Time
  while guiding (do we need to disable it?).
- Get rid of GuideModel and related obsolete cruft.

To do:
- Think about a fix for the various params when an image hasn't been
  downloaded yet -- what value to show during that process?
  
- Add a notation to non-guide images that are shown while guiding.
- Add some kind of display of what guide correction was made;
  preferably a graph that shows a history of guide corrections
  perhaps as a series of linked(?) lines, with older ones dimmer until fade out?
- Add snap points for dragging along slit -- a big job
- Work with Craig to handle "expired" images better.
  These are images that can no longer be used for guiding
  because the telescope has moved.
- Add preference to limit # of images saved to disk.
  Include an option to keep images on quit or ask, or always just delete?


History:
2005-02-10 ROwen    alpha version; lots of work to do
2005-02-22 ROwen    Added drag to centroid. Modified for GryImageDispWdg 2005-02-22.
2005-02-23 ROwen    Added exposure time; first cut at setting exp time and thresh when a new image comes in.
2005-03-28 ROwen    Modified for improved files and star keywords.
2005-03-31 ROwen    Implemented hub commands. Added display of current image name.
2005-04-11 ROwen    Modified for GCamModel->guiderModel
2005-04-12 ROwen    Added display of data about selected star.
                    Improved to run in normal mode by default and local mode during tests.
2005-04-13 ROwen    Added Stop Guiding and Guide On Boresight.
                    Bug fix: mis-handled star data when multiple images used the same (cmdr,cmdID).
2005-04-15 ROwen    Modified to set exposure time and bin factor from the fits image header.
                    Modified to send exposure time and bin factor in commands that expose.
                    Bug fix: displayed new annotations on the wrong image while the new image was downloading.
2005-04-18 ROwen    Modified to only download guide images if this widget is visible.
                    Modified to delete images from disk when they fall off the history list
                    or when the application exits (but not in local test mode).
                    Initial default exposure time and bin factor are now set from the model.
                    Modified to use updated test code.
2005-04-21 ROwen    Added control-click to center on a point and removed the center Button.
                    Most errors now write to the status bar (imageRoot unknown is still an exception).
2005-04-26 ROwen    Added preliminary history navigation; it needs some cleanup.
                    Added attribute "deviceSpecificFrame" for device-specific controls.
2005-04-27 ROwen    Finished logic for history controls.
                    Finished error handling in BasicImObj.
2005-05-13 ROwen    Added preliminary support for manual guiding.
                    Re-added the Center button.
                    Added references to html help.
                    Mod. to pack the widgets instead of gridding them.
                    Added _DebugMem flag and commented out the remaining
                    non-flag-protected diagnostic print statement.
2005-05-20 ROwen    Bug fix: was not setting ImObj.defThresh on creation.
                    But fix: set ImObj.currThresh to None instead of default if curr thresh unknown.
                    Bug fix: layout was messed up by going to the packer so reverted to gridder.
                    (The space for multiple widgets with expand=True is always shared
                    even if some of them only grow in one direction. Truly hideous!)
                    Bug fix: the history controls were always disabled.
2005-05-23 ROwen    Mod. to overwrite image files if new ones come in with the same name;
                    this simplifies debugging and corrects bugs associated with the old way
                    (the new image's ImObj would replace the old one, so the old one
                    was never accessible and never deleted).
                    Bug fix: typo in code that handled displaying unavailable images.
2005-05-26 ROwen    Cleaned up button enable/disable.
                    Added doCmd method to centralize command execution.
2005-06-09 ROwen    Added more _DebugMem output.
                    Apparently fixed a bug that prevented file delete for too-old files.
2005-06-10 ROwen    Modified for noStarsFound->noGuideStar in guide model.
                    Also changed the no stars message to "Star Not Found".
2005-06-13 ROwen    Bug fix: one of the delete delete messages was mis-formatted.
                    Added more memory tracking code.
                    Modified test code to download images from APO.
2005-06-15 ROwen    Added Choose... button to open any fits file.
                    Modified so displayed image is always in history list;
                    also if there is a gap then the history buttons show it.
2005-06-16 ROwen    Changed to not use a command status bar for manual guiding.
                    Modified _guideStateCallback to use new KeyVar getSeverity method.
                    Modified to only import GuideTest if in test mode.
                    Bug fix: isGuiding usually returned False even if true.
                    Bug fix: dragStar used as method name and attribute (found by pychecker).
2005-06-17 ROwen    Bug fix: mis-handled Cancel in Choose... dialog.
                    Bug fix: pyfits.open can return [] for certain kinds of invalid image files,
                    instead of raising an exception (presumably a bug in pyfits).
                    This case is now handled properly.
                    Manual centroid was sending radius instead of cradius.
2005-06-21 ROwen    Overhauled command buttons: improved layout and better names.
                    Removed the Center button (use control-click).
                    Changed appearance of the "Current" button to make it clearer.
                    Moved guiding status down to just above the status bar.
2005-06-22 ROwen    Moved guiding status back to the top.
                    Changed display of current image name to a read-only entry; this fixed
                    a resize problem and allows the user to scroll to see the whole name.
2005-06-23 ROwen    Added logic to disable the currently active command button.
                    Added a Cancel button to re-enable buttons when things get stuck.
                    Improved operation while guide window closed: image info
                    is now kept in the history as normal, but download is deferred
                    until the user displays the guide window and tries to look at an image.
                    Images that cannot be displayed now show the reason
                    in the middle of the image area, instead of in the status bar.
                    Tweaked definition of isGuiding to better match command enable;
                    now only "off" is not guiding; formerly "stopping" was also not guiding.
2005-06-24 ROwen    Modified to use new hub manual guider.
                    Added show/hide Image button.
                    Modified the way exposure parameters are updated: now they auto-track
                    the current value if they are already current. But as soon as you
                    change one, the change sticks. This is in preparation for
                    support of guiding tweaks.
                    Modified to not allow guiding on a star from a non-current image
                    (if the guider is ever smart enough to invalidate images
                    once the telescope has moved, this can be handled more flexibly).
                    Bug fix in test code; GuideTest not setting _LocalMode.
                    Bug fix: current image name not right-justified after shrinking window.
2005-06-27 ROwen    Removed image show/hide widget for now; I want to straighten out
                    the resize behavior and which other widgets to hide or disable
                    before re-enabling this feature.
                    Added workaround for bug in tkFileDialog.askopenfilename on MacOS X.
2005-07-08 ROwen    Modified for http download.
2005-07-14 ROwen    Removed _LocalMode and local test mode support.
2005-09-28 ROwen    The DS9 button shows an error in the status bar if it fails.
2005-11-09 ROwen    Fix PR 311: traceback in doDragContinue, unscriptable object;
                    presumably self.dragStar was None (though I don't know how).
                    Improved doDragContinue to null dragStar, dragRect on error.
2006-04-07 ROwen    In process of overhauling guider; some tests work
                    but more tests are wanted.
                    Removed tracking of mask files because the mask is now contained in guide images.
                    Bug fix: _guideStateCallback was mis-called.
                    Re-added "noGuide" to centerOn commands to improve compatibility with old guide code.
2006-04-11 ROwen    Display boresight (if available).
                    Disable some controls when holding an image, and make it clear it's happening.
                    Bug fix: mode widget not getting correctly set when a new mode seen.
2006-04-13 ROwen    Added support for bad pixel and saturated pixel masks.
                    Changed centering commands from "guide on centerOn=x,y noGuide..."
                    to "guide centrOn=x,y...". Thanks for the simpler command, Craig!
2006-04-14 ROwen    Tweaked guide mode widget names and label.
                    Does not display a selected star in manual guide mode,
                    but maybe this stops a centroid from selecting itself in that mode?
                    Bug fix: the Apply button was not grayed out while operating.
2006-04-17 ROwen    Fix PR 393: ctrl-click guider offsets need to specify exposure time.
2006-04-21 ROwen    Bug fix: the Apply button's command called doCmd with isGuideOn=True.
2006-04-26 ROwen    Bug fix: two tests involving an image's defSelDataColor could fail
                    if there was no selection.
2006-04-27 ROwen    Bug fixes (thanks to pychecker):
                    - e missing from "except <exception>, e" in two error handlers.
                    - centerBtn -> self.centerBtn in doCenterOnSel.
                    - defGuideMode not set on new image objects.
2006-05-04 ROwen    Modified Cancel to clear self.doingCmd and call enableCmdButtons,
                    rather than relying on the command's abort method to do this.
                    This may make cancel a bit more reliable about enabling buttons.
                    Added _DebugBtnEnable to help diagnose button enable errors.
                    Clarified some code comments relating to self.doingCmd.
2006-05-19 ROwen    Overhauled the way commands are tied to images.
                    Added display of predicted guide star position.
                    Guide star(s) are now shown as distinct from other stars.
2006-05-19 ROwen    Modified to select the (first) guide star, thus displaying FWHM.
                    (If the guide star is missing, the first found star will be selected instead.)
                    Modified to always show centroid stars above guide stars above found stars.
                    Added support for color preferences.
                    Modified Current to restore selected star.
                    Bug fix: NA2 guider would not show Apply after selecting a star
                    (I'm not sure why any guider would, but I fixed it).
                    Bug fix: Current broken on NA2 guider due to method name conflict.
2006-05-24 ROwen    Changed non-slitviewer Star mode to Field Star for consistency.
2006-06-29 ROwen    Added imDisplayed method and modified code to use it;
                    this is more reliable than the old test of self.dispImObj not None.
                    This fixes a bug whereby DS9 is enabled but cannot send an image.
                    Started adding support for subframing, but much remains to be done;
                    meanwhile the new widgets are not yet displayed.
2006-08-03 ROwen    Moved ImObj class to its own file Image.py and renamed it to GuideImage.
2006-09-26 ROwen    Added subframe (CCD window) support.
2006-10-11 ROwen    Added explicit default for GuideMode.
2006-10-31 ROwen    Fixed incorrect units in one FWHM help text string.
2006-11-06 ROwen    Modified to use new definition of <x>cam window argument.
2007-01-11 ROwen    Bug fix: Thresh and Rad Mult limits not being tested
                    due to not using the doneFunc argument of RO.Wdg.Entry widgets.
                    Used the new label argument for RO.Wdg.Entry widgets.
2007-04-24 ROwen    Modified to use numpy instead of numarray.
2007-12-18 ROwen    Improved control-click offset: display an arrow showing the offset; the arrow
                    may be dragged to modify the offset or dragged off the image to cancel the offset.
2007-01-28 ROwen    Changed default range from 99.9% to 99.5%.
2008-02-11 ROwen    Changed name of cancel button from Cancel to X.
2008-03-28 ROwen    Fix PR 772: ctrl-click arrow stopped updating if ctrl key lifted.
2008-04-01 ROwen    Fix PR 780: ctrl-click fails; I was testing the truth value of an array.
                    Modified to cancel control-click if control key released.
2008-04-22 ROwen    Added display of exposure status.
2008-04-23 ROwen    Modified to accept expState durations of None as unknown.
2008-04-28 ROwen    Modified to only download one guide image at a time
                    when auto-downloading current images (if you go back in history
                    to view skipped images you can easily start multiple downloads).
2008-04-29 ROwen    Fixed reporting of exceptions that contain unicode arguments.
                    Bug fix: could download the same image twice.
2008-05-15 ROwen    Modified to use new doStretch argument for MaskInfo.
2009-04-01 ROwen    Modified to use opscore.actor.keyvar instead of RO.KeyVariable.
                    Modified to use reactor timer instead of Tk timer.
2009-07-14 ROwen    Added support for bad pixel mask.
2009-07-17 ROwen    Removed slitviewer support.
2009-09-11 ROwen    Partial implementation for SDSS3.
"""
import atexit
import os
import sys
import weakref
import Tkinter
import tkFileDialog
import numpy
import RO.Alg
import RO.Constants
import RO.DS9
import RO.OS
import RO.Prefs
import RO.StringUtil
import RO.Wdg
import RO.Wdg.GrayImageDispWdg as GImDisp
import opscore.actor.keyvar
import TUI.Base.Wdg
import TUI.Models.TUIModel
import GuideImage
import TUI.Models.GuiderModel

_HelpPrefix = "Guiding/index.html#"

_MaxDist = 15
_CentroidTag = "centroid"
_FindTag = "findStar"
_GuideTag = "guide"
_SelTag = "showSelection"
_DragRectTag = "centroidDrag"
_BoreTag = "boresight"

_SelRad = 18
_SelHoleRad = 9
_BoreRad = 6
_GuideRad = 18
_GuideHoleRad = 9
_GuidePredPosRad = 9

_HistLen = 100

_DebugMem = False # print a message when a file is deleted from disk?
_DebugBtnEnable = True # print messages that help debug button enable?

_HelpURL = None

class CmdInfo(object):
    """Information about an image-related command"""
    Centroid = "c"
    Findstars = "f"
    def __init__(self,
        cmdr,
        cmdID,
        imObj,
        isNewImage,
    ):
        self.cmdr = cmdr
        self.cmdID = cmdID
        self.imObj = imObj
        self.isNewImage = isNewImage
        
        self._sawStarData = set()
    
    def sawStarData(self, dataType):
        """Set sawStarData flag for the specified dataType and return old value of flag.
        dataType is a character from the star keyword; it is presently one of "c", "f" or "g".
        """
        dataType = dataType.lower()
        retVal = dataType in self._sawStarData
        self._sawStarData.add(dataType)
        return retVal

    def _clear(self):
        """Clear any data that might cause memory leaks"""
        self.imObj = None


class CurrCmds(object):
    """Information about all current image-related commands"""
    def __init__(self, timeLim=60):
        self.timeLim = timeLim
        self.currCmds = dict() # dict of (cmdr, cmdID): CmdInfo
        self.tuiModel = TUI.Models.TUIModel.Model()
    
    def addCmd(self, cmdr, cmdID, imObj, isNewImage):
        cmdInfo = CmdInfo(
            cmdr = cmdr,
            cmdID = cmdID,
            imObj = imObj,
            isNewImage = isNewImage
        )
        self.currCmds[(cmdr, cmdID)] = cmdInfo
        self.tuiModel.reactor.callLater(self.timeLim, self.delCmdInfo, cmdInfo.cmdr, cmdInfo.cmdID)
    
    def getCmdInfo(self, cmdr, cmdID):
        """Return cmdInfo, or None if no such command."""
        return self.currCmds.get((cmdr, cmdID), None)
    
    def getCmdInfoFromKeyVar(self, keyVar):
        """Return cmdInfo based on keyVar, or None if no such command."""
        cmdr, cmdID = keyVar.getCmdrCmdID()
        return self.getCmdInfo(cmdr, cmdID)
        
    def delCmdInfo(self, cmdr, cmdID):
        #print "deleting cmd (%s, %s)" % (cmdr, cmdID)
        cmdInfo = self.currCmds.pop((cmdr, cmdID), None)
        if cmdInfo:
            cmdInfo._clear()


class HistoryBtn(RO.Wdg.Button):
    _InfoDict = {
        (False, False): ("show previous image", u"\N{BLACK LEFT-POINTING TRIANGLE}"),
        (False, True):  ("show previous OUT OF SEQUENCE image", u"\N{WHITE LEFT-POINTING TRIANGLE}"),
        (True,  False): ("show next image", u"\N{BLACK RIGHT-POINTING TRIANGLE}"),
        (True,  True):  ("show next OUT OF SEQUENCE image", u"\N{WHITE RIGHT-POINTING TRIANGLE}"),
    }
    def __init__(self,
        master,
        isNext = True,
    **kargs):
        self.isNext = bool(isNext)
        self.isGap = False
        if self.isNext:
            self.descr = "next"
        else:
            self.descr = "previous"
        RO.Wdg.Button.__init__(self, master, **kargs)
        self._redisplay()
    
    def setState(self, doEnable, isGap):
        self.setEnable(doEnable)
        if self.isGap == bool(isGap):
            return
        self.isGap = bool(isGap)
        self._redisplay()
    
    def _redisplay(self):
        self.helpText, btnText = self._InfoDict[(self.isNext, self.isGap)]
        self["text"] = btnText


class GuideWdg(Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)
        
        self.actor = "guider"
        self.guiderModel = TUI.Models.GuiderModel.Model()
        self.tuiModel = TUI.Models.TUIModel.Model()
        self.dragStart = None
        self.dragRect = None
        self.exposing = None # True, False or None if unknown
        self.currDownload = None # image object being downloaded
        self.nextDownload = None # next image object to download
        self.settingEnable = False
        
        # color prefs
        def getColorPref(prefName, defColor, isMask = False):
            """Get a color preference. If not found, make one."""
            pref = self.tuiModel.prefs.getPrefVar(prefName, None)
            if pref == None:
                pref = RO.Prefs.PrefVar.ColorPrefVar(
                    name = prefName,
                    defValue = "cyan",
                )
            if isMask:
                pref.addCallback(self.updMaskColor, callNow=False)
            else:
                pref.addCallback(self.redisplayImage, callNow=False)
            return pref
        
        self.typeTagColorPrefDict = {
            "c": (_CentroidTag, getColorPref("Centroid Color", "cyan")),
            "f": (_FindTag, getColorPref("Found Star Color", "green")),
            "g": (_GuideTag, getColorPref("Guide Star Color", "magenta")),
        }
        self.boreColorPref = getColorPref("Boresight Color", "cyan")
        self.maskColorPrefs = ( # for sat, bad and masked pixels
            getColorPref("Saturated Pixel Color", "red", isMask = True),
            getColorPref("Bad Pixel Color", "red", isMask = True),
            getColorPref("Masked Pixel Color", "green", isMask = True),
        )
        
        self.nToSave = _HistLen # eventually allow user to set?
        self.imObjDict = RO.Alg.ReverseOrderedDict()
        self._memDebugDict = {}
        self.dispImObj = None # object data for most recently taken image, or None
        self.ds9Win = None
        
        self.doingCmd = None # (cmdVar, cmdButton, isGuideOn) used for currently executing cmd
        self._btnsLaidOut = False
        
        self.currCmds = CurrCmds()
        
        totCols = 4
        
        row=0

        helpURL = _HelpPrefix + "GuidingStatus"

        guideStateFrame = Tkinter.Frame(self)
        gsGridder = RO.Wdg.Gridder(guideStateFrame, sticky="w")
        
        self.guideStateWdg = RO.Wdg.StrLabel(
            master = guideStateFrame,
            formatFunc = str.capitalize,
            anchor = "w",
            helpText = "Current state of guiding",
            helpURL = helpURL,
        )
        gsGridder.gridWdg("Guiding", self.guideStateWdg, colSpan=2)

        self.expStateWdg = RO.Wdg.StrLabel(
            master = guideStateFrame,
            helpText = "Status of current exposure",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
        self.expTimer = RO.Wdg.TimeBar(
            master = guideStateFrame,
            valueFormat = "%3.1f sec",
            isHorizontal = True,
            autoStop = True,
            helpText = "Status of current exposure",
            helpURL = helpURL,
        )
        gsGridder.gridWdg("Exp Status", (self.expStateWdg, self.expTimer), sticky="ew")
        self.expTimer.grid_remove()
        
        guideStateFrame.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        guideStateFrame.columnconfigure(2, weight=1)
        row += 1

        helpURL = _HelpPrefix + "HistoryControls"
        
        histFrame = Tkinter.Frame(self)
        
        self.showHideImageWdg = RO.Wdg.Checkbutton(
            histFrame,
            text = "Image",
            #onvalue = "Hide",
            #offvalue = "Show",
            #showValue = True,
            #width = 4,
            indicatoron = False,
            defValue = True,
            callFunc = self.doShowHideImage,
            helpText = "Show or hide image",
            helpURL = helpURL,
        )
        #self.showHideImageWdg.pack(side="left")
        
        self.prevImWdg = HistoryBtn(
            histFrame,
            isNext = False,
            callFunc = self.doPrevIm,
            helpURL = helpURL,
        )
        self.prevImWdg.pack(side="left")
        
        self.nextImWdg = HistoryBtn(
            histFrame,
            isNext = True,
            callFunc = self.doNextIm,
            helpURL = helpURL,
        )
        self.nextImWdg.pack(side="left")
        
        onOffVals = ("Current", "Hold")
        lens = [len(val) for val in onOffVals]
        maxLen = max(lens)
        self.showCurrWdg = RO.Wdg.Checkbutton(
            histFrame,
#           text = "Current",
            defValue = True,
            onvalue = onOffVals[0],
            offvalue = onOffVals[1],
            width = maxLen,
            showValue = True,
            callFunc = self.doShowCurr,
            helpText = "Display current image?",
            helpURL = helpURL,
        )
        self.showCurrWdg.pack(side="left")
        
        self.chooseImWdg = RO.Wdg.Button(
            histFrame,
            text = "Choose...",
            callFunc = self.doChooseIm,
            helpText = "Choose a fits file to display",
            helpURL = helpURL,
        )
        self.chooseImWdg.pack(side="right")
        
        self.imNameWdg = RO.Wdg.StrEntry(
            master = histFrame,
            justify="right",
            readOnly = True,
            helpText = "Name of displayed image",
            helpURL = helpURL,
            )
        self.imNameWdg.pack(side="left", expand=True, fill="x", padx=4)
        
        def showRight(evt=None):
            self.imNameWdg.xview("end")
        self.imNameWdg.bind("<Configure>", showRight)
        
        histFrame.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1
        
        maskInfo = (
            GImDisp.MaskInfo(
                bitInd = 0,
                name = "saturated pixels",
                btext = "Sat",
                color = self.maskColorPrefs[0].getValue(),
                intens = 255,
                doStretch = True,
            ),
            GImDisp.MaskInfo(
                bitInd = 1,
                name = "bad pixels",
                btext = "Bad",
                color = self.maskColorPrefs[1].getValue(),
                intens = 255,
                doStretch = False,
            ),
            GImDisp.MaskInfo(
                bitInd = 2,
                name = "masked pixels",
                btext = "Mask",
                color = self.maskColorPrefs[2].getValue(),
                intens = 100,
                doStretch = False,
            ),
        )

        self.gim = GImDisp.GrayImageWdg(self,
            maskInfo = maskInfo,
            helpURL = _HelpPrefix + "Image",
            defRange = "99.5%",
        )
        self.plateBtn = RO.Wdg.Checkbutton(
            master = self.gim.toolFrame,
            indicatoron = False,
            text = "Plate",
            defValue = False, # elsewhere set this to True if the image has plate info
            callFunc = self.togglePlateView,
            helpText = "Show plate view of guide probes or normal image",
        )
        self.plateBtn.pack(side="left")
        self.gim.grid(row=row, column=0, columnspan=totCols, sticky="news")
        self.grid_rowconfigure(row, weight=1)
        self.grid_columnconfigure(totCols - 1, weight=1)
        row += 1
        
        self.defCnvCursor = self.gim.cnv["cursor"]
        
        helpURL = _HelpPrefix + "DataPane"
        
        starFrame = Tkinter.Frame(self)

        RO.Wdg.StrLabel(
            starFrame,
            text = " Star ",
            bd = 0,
            padx = 0,
            helpText = "Information about the selected star",
            helpURL = helpURL,
        ).pack(side="left")
        
        RO.Wdg.StrLabel(
            starFrame,
            text = "Pos: ",
            bd = 0,
            padx = 0,
            helpText = "Centroid of the selected star (pix)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starXPosWdg = RO.Wdg.FloatLabel(
            starFrame,
            width = 6,
            precision = 1,
            anchor="e",
            bd = 0,
            padx = 0,
            helpText = "X centroid of selected star (pix)",
            helpURL = helpURL,
        )
        self.starXPosWdg.pack(side="left")
        
        RO.Wdg.StrLabel(
            starFrame,
            text = ", ",
            bd = 0,
            padx = 0,
        ).pack(side="left")
        self.starYPosWdg = RO.Wdg.FloatLabel(
            starFrame,
            width = 6,
            precision = 1,
            anchor="e",
            bd = 0,
            padx = 0,
            helpText = "Y centroid of selected star (pix)",
            helpURL = helpURL,
        )
        self.starYPosWdg.pack(side="left")

        RO.Wdg.StrLabel(
            starFrame,
            text = "  FWHM: ",
            bd = 0,
            padx = 0,
            helpText = "FWHM of selected star (pix)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starFWHMWdg = RO.Wdg.FloatLabel(
            starFrame,
            width = 4,
            precision = 1,
            anchor="e",
            bd = 0,
            padx = 0,
            helpText = "FWHM of selected star (pix)",
            helpURL = helpURL,
        )
        self.starFWHMWdg.pack(side="left")

        RO.Wdg.StrLabel(
            starFrame,
            text = "  Ampl: ",
            bd = 0,
            padx = 0,
            helpText = "Amplitude of selected star (ADUs)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starAmplWdg = RO.Wdg.FloatLabel(
            starFrame,
            width = 7,
            precision = 1,
            anchor="e",
            bd = 0,
            padx = 0,
            helpText = "Amplitude of selected star (ADUs)",
            helpURL = helpURL,
        )
        self.starAmplWdg.pack(side="left")
        
        RO.Wdg.StrLabel(
            starFrame,
            text = "  Bkgnd: ",
            bd = 0,
            padx = 0,
            helpText = "Background level at selected star (ADUs)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starBkgndWdg = RO.Wdg.FloatLabel(
            starFrame,
            width = 6,
            precision = 1,
            anchor="e",
            bd = 0,
            padx = 0,
            helpText = "Background level at selected star (ADUs)",
            helpURL = helpURL,
        )
        self.starBkgndWdg.pack(side="left")

        starFrame.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1
        
        helpURL = _HelpPrefix + "AcquisitionControls"
        
        inputFrame1 = Tkinter.Frame(self)

        helpText = "exposure time"
        RO.Wdg.StrLabel(
            inputFrame1,
            text = "Exp Time",
            helpText = helpText,
            helpURL = helpURL,
        ).pack(side="left")
        
        self.expTimeWdg = RO.Wdg.FloatEntry(
            inputFrame1,
            label = "Exp Time",
            minValue = 0.0,
            defValue = 5.0,
            defFormat = "%.1f",
            defMenu = "Current",
            minMenu = "Minimum",
            autoIsCurrent = True,
            helpText = helpText,
            helpURL = helpURL,
        )
        self.expTimeWdg.pack(side="left")

        RO.Wdg.StrLabel(
            inputFrame1,
            text = "sec  Enable",
            anchor = "w",
        ).pack(side="left")

        self.axesEnableWdg = RO.Wdg.Checkbutton(
            master = inputFrame1,
            text = "Axes",
            defValue = True,
            callFunc = self.doEnableCorrection,
            helpText = "Enable correction of az, alt and rot axes",
            helpURL = _HelpURL,
        )
        self.axesEnableWdg.pack(side="left")
        self.focusEnableWdg =  RO.Wdg.Checkbutton(
            master = inputFrame1,
            text = "Focus",
            defValue = True,
            callFunc = self.doEnableCorrection,
            helpText = "Enable correction of focus",
            helpURL = _HelpURL,
        )
        self.focusEnableWdg.pack(side="left")
        self.scaleEnableWdg =  RO.Wdg.Checkbutton(
            master = inputFrame1,
            text = "Scale",
            defValue = True,
            callFunc = self.doEnableCorrection,
            helpText = "Enable correction of plate scale",
            helpURL = _HelpURL,
        )
        self.scaleEnableWdg.pack(side="left")
        
        inputFrame1.grid(row=row, column=0, sticky="ew")
        row += 1

        guideEnableFrame = Tkinter.Frame(self)
        

        self.currentBtn = RO.Wdg.Button(
            guideEnableFrame,
            text = "Current",
            command = self.doCurrent,
            helpText = "Show current guide parameters",
            helpURL = helpURL,
        )
        self.currentBtn.pack(side="right")
        
        guideEnableFrame.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1

        self.guideParamWdgSet = [
            self.expTimeWdg,
        ]
        for wdg in self.guideParamWdgSet:
            wdg.addCallback(self.enableCmdButtons)

        self.devSpecificFrame = Tkinter.Frame(self)
        self.devSpecificFrame.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1

        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = _HelpPrefix + "StatusBar",
        )
        self.statusBar.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1
        
        helpURL = _HelpPrefix + "GuidingControls"
        
        cmdButtonFrame = Tkinter.Frame(self)
        cmdCol = 0
        self.exposeBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Expose",
            callFunc = self.doExpose,
            helpText = "Take an exposure",
            helpURL = helpURL,
        )
        
        self.centerBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Center",
            callFunc = self.doCenterOnSel,
            helpText = "Put selected star on the boresight",
            helpURL = helpURL,
        )
        
        self.guideOnBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Guide",
            callFunc = self.doGuideOn,
            helpText = "Start guiding",
            helpURL = helpURL,
        )
        
        self.applyBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Apply",
            callFunc = self.doGuideTweak,
            helpText = "Apply new guide parameters",
            helpURL = helpURL,
        )

        self.guideOffBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Stop Guiding",
            callFunc = self.doGuideOff,
            helpText = "Turn off guiding",
            helpURL = helpURL,
        )
        
        self.cancelBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "X",
            callFunc = self.cmdCancel,
            helpText = "Cancel executing command",
            helpURL = helpURL,
        )
        
        self.ds9Btn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "DS9",
            callFunc = self.doDS9,
            helpText = "Display image in ds9",
            helpURL = helpURL,
        )

        self.holdWarnWdg = RO.Wdg.StrLabel(
            cmdButtonFrame,
            text = "Holding Image",
            severity = RO.Constants.sevWarning,
            anchor = "center",
            helpText = "Press Hold above to enable these controls",
        )
        
        # lay out command buttons
        col = 0
        self.exposeBtn.grid(row=0, column=col)
        self.holdWarnWdg.grid(row=0, column=col, columnspan=totCols, sticky="ew")
        self.holdWarnWdg.grid_remove()
        col += 1
        self.guideOnBtn.grid(row=0, column=col)
        col += 1
        self.applyBtn.grid(row=0, column=col)
        col += 1
        self.guideOffBtn.grid(row=0, column=col)
        col += 1
        self.cancelBtn.grid(row=0, column=col)
        col += 1
        self.ds9Btn.grid(row=0, column=col, sticky="e")
        cmdButtonFrame.grid_columnconfigure(col, weight=1)
        col += 1
        # leave room for the resize control
        Tkinter.Label(cmdButtonFrame, text=" ").grid(row=0, column=col)
        col += 1
        
        # enable controls accordingly
        self.enableCmdButtons()
        self.enableHistButtons()

        cmdButtonFrame.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1
        
        # event bindings
        self.gim.bind("<Map>", self.doMap)

        self.gim.cnv.bind("<Button-1>", self.doDragStart, add=True)
        self.gim.cnv.bind("<B1-Motion>", self.doDragContinue, add=True)
        self.gim.cnv.bind("<ButtonRelease-1>", self.doDragEnd, add=True)
        
        # keyword variable bindings
# there is no expState keyword yet
#        self.guiderModel.expState.addCallback(self._expStateCallback)
        self.guiderModel.files.addCallback(self._filesCallback)
        self.guiderModel.guideEnable.addCallback(self._guideEnableCallback)
        self.guiderModel.guideState.addCallback(self._guideStateCallback)

        # bindings to set the image cursor
        tl = self.winfo_toplevel()
        tl.bind("<Control-KeyPress>", self.cursorCtr, add=True)
        tl.bind("<Control-KeyRelease>", self.ignoreEvt, add=True)
        tl.bind("<KeyRelease>", self.cursorNormal, add=True)
        
        # exit handler
        atexit.register(self._exitHandler)
        
        self.enableCmdButtons()
        self.enableHistButtons()

    def _trackMem(self, obj, objName):
        """Print a message when an object is deleted.
        """
        if not _DebugMem:
            return
        objID = id(obj)
        def refGone(ref=None, objID=objID, objName=objName):
            print "GuideWdg deleting %s" % (objName,)
            del(self._memDebugDict[objID])

        self._memDebugDict[objID] = weakref.ref(obj, refGone)
        del(obj)

    def addImToHist(self, imObj, ind=None):
        imageName = imObj.imageName
        if ind == None:
            self.imObjDict[imageName] = imObj
        else:
            self.imObjDict.insert(ind, imageName, imObj)
    
    def areParamsModified(self):
        """Return True if any guiding parameter has been modified"""
        for wdg in self.guideParamWdgSet:
            if not wdg.getIsCurrent():
                return True
        
        if self.dispImObj and self.dispImObj.defSelDataColor and self.dispImObj.selDataColor \
            and (self.dispImObj.defSelDataColor[0] != self.dispImObj.selDataColor[0]):
            # star selection has changed
            return True

        return False

    def cmdCancel(self, wdg=None):
        """Cancel the current command.
        """
        if _DebugBtnEnable:
            print "cmdCancel(wdg=%s); self.doingCmd=%s" % (wdg, self.doingCmd,)
        if self.doingCmd == None:
            return
        cmdVar = self.doingCmd[0]
        cmdVar.abort()
        self.doingCmd = None
        self.enableCmdButtons()

    def cmdCallback(self, cmdVar):
        """Use this callback when launching a command
        whose completion requires buttons to be re-enabled.
        
        DO NOT use as the sole means of re-enabling guide on button(s)
        because if guiding turns on successfully, the command is not reported
        as done until guiding is terminated.
        """
        if _DebugBtnEnable:
            print "cmdCallback(cmdVar=%s); self.doingCmd=%s" % (cmdVar, self.doingCmd,)
        if self.doingCmd == None:
            return
        if self.doingCmd[0] == cmdVar:
            cmdBtn = self.doingCmd[1]
            if cmdBtn != None:
                cmdBtn.setEnable(True)
            if cmdVar.didFail:
                failFunc = self.doingCmd[3]
                if failFunc:
#                    print "command failed; calling failFunc=%s" % (failFunc,)
                    failFunc()
            self.doingCmd = None
        else:
            sys.stderr.write("GuideWdg warning: cmdCallback called for wrong cmd:\n- doing cmd: %s\n- called by cmd: %s\n" % (self.doingCmd[0], cmdVar))
        self.enableCmdButtons()

    def cursorCtr(self, evt=None):
        """Show image cursor for "center on this point".
        """
        self.gim.cnv["cursor"] = "crosshair"
    
    def cursorNormal(self, evt=None):
        """Show normal image cursor and reset control-click if present
        """
        self.gim.cnv["cursor"] = self.defCnvCursor

    def doCenterOnSel(self, evt):
        """Center up on the selected star.
        """
        try:
            if not self.imDisplayed():
                raise RuntimeError("No guide image")

            if not self.dispImObj.selDataColor:
                raise RuntimeError("No star selected")
            
            starData = self.dispImObj.selDataColor[0]
            pos = starData[2:4]
    
            starArgs = self.getSelStarArgs(posKey="centerOn")
            expArgs = self.getExpArgStr()
            cmdStr = "guide %s %s" % (starArgs, expArgs)
        except RuntimeError, e:
            self.statusBar.setMsg(RO.StringUtil.strFromException(e), severity = RO.Constants.sevError)
            self.statusBar.playCmdFailed()
            return

        self.doCmd(
            cmdStr = cmdStr,
            cmdBtn = self.centerBtn,
        )
    
    def doChooseIm(self, wdg=None):
        """Choose an image to display.
        """
        self.showCurrWdg.setBool(False)

        if self.dispImObj != None:
            currPath = self.dispImObj.localPath
            startDir, startFile = os.path.split(currPath)
        else:
            # use user preference for image directory, if available
            startDir = self.tuiModel.prefs.getValue("Save To")
            startFile = None

        # work around a bug in Mac Aqua tkFileDialog.askopenfilename
        # for unix, invalid dir or file are politely ignored
        # but either will cause the dialog to fail on MacOS X
        kargs = {}
        if startDir != None and os.path.isdir(startDir):
            kargs["initialdir"] = startDir
            if startFile != None and os.path.isfile(os.path.join(startDir, startFile)):
                kargs["initialfile"] = startFile

        imPath = tkFileDialog.askopenfilename(
            filetypes = (("FITS", "*.fits"), ("FITS", "*.fit"),),
        **kargs)
        if not imPath:
            return
            
        self.showFITSFile(imPath)
    
    def doCurrent(self, wdg=None):
        """Restore default value of all guide parameter widgets"""
        for wdg in self.guideParamWdgSet:
            wdg.restoreDefault()
        
        if self.dispImObj and self.dispImObj.defSelDataColor and self.dispImObj.selDataColor \
            and (self.dispImObj.defSelDataColor[0] != self.dispImObj.selDataColor[0]):
            # star selection has changed
            self.dispImObj.selDataColor = self.dispImObj.defSelDataColor
            self.showSelection()
    
    def showFITSFile(self, imPath):
        """Display a FITS file.
        """     
        # try to find image in history
        # using samefile is safer than trying to match paths as strings
        # (RO.OS.expandPath *might* be thorough enough to allow that,
        # but no promises and one would have to expand every path being checked)
        for imObj in self.imObjDict.itervalues():
            try:
                isSame = os.path.samefile(imPath, imObj.localPath)
            except OSError:
                continue
            if isSame:
                self.showImage(imObj)
                return
        # not in history; create new local imObj and load that

        # try to split off user's base dir if possible
        localBaseDir = ""
        imageName = imPath
        startDir = self.tuiModel.prefs.getValue("Save To")
        if startDir != None:
            startDir = RO.OS.expandPath(startDir)
            if startDir and not startDir.endswith(os.sep):
                startDir = startDir + os.sep
            imPath = RO.OS.expandPath(imPath)
            if imPath.startswith(startDir):
                localBaseDir = startDir
                imageName = imPath[len(startDir):]
        
        #print "localBaseDir=%r, imageName=%r" % (localBaseDir, imageName)
        imObj = GuideImage.GuideImage(
            localBaseDir = localBaseDir,
            imageName = imageName,
            isLocal = True,
        )
        self._trackMem(imObj, str(imObj))
        imObj.fetchFile()
        ind = None
        if self.dispImObj != None:
            try:
                ind = self.imObjDict.index(self.dispImObj.imageName)
            except KeyError:
                pass
        self.addImToHist(imObj, ind)
        self.showImage(imObj)
        
    def doCmd(self,
        cmdStr,
        cmdBtn = None,
        isGuideOn = False,
        actor = None,
        abortCmdStr = None,
        cmdSummary = None,
        failFunc = None,
    ):
        """Execute a command.
        Inputs:
        - cmdStr        the command to execute
        - cmdBtn        the button that triggered the command
        - isGuideOn     set True for commands that start guiding; ignored if cmdBtn omitted
        - actor         the actor to which to send the command;
                        defaults to the actor for the guide camera
        - abortCmdStr   abort command, if any
        - cmdSummary    command summary for the status bar
        - failFunc      function to execute if the command fails or is cancelled; ignored if cmdBtn omitted
        """
        actor = actor or self.actor
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = actor,
            cmdStr = cmdStr,
            abortCmdStr = abortCmdStr,
        )
        if cmdBtn:
            self.doingCmd = (cmdVar, cmdBtn, isGuideOn, failFunc)
            cmdVar.addCallback(
                self.cmdCallback,
                callCodes = opscore.actor.keyvar.DoneCodes,
            )
        else:
            self.doingCmd = None
        self.enableCmdButtons()
        self.statusBar.doCmd(cmdVar, cmdSummary)
    
#     def doExistingImage(self, imageName, cmdr, cmdID):
#         """Data is about to arrive for an existing image.
#         Decide whether we are interested in it,
#         and if so, get ready to receive it.
#         """
#         #print "doExistingImage(imageName=%r, cmdr=%r, cmdID=%r" % (imageName, cmdr, cmdID)
#         # see if this data is of interest
#         imObj = self.imObjDict.get(imageName)
#         if not imObj:
#             # I have no knowledge of this image, so ignore the data
#             return
#         isMe = (cmdr == self.tuiModel.getCmdr())
#         if not isMe:
#             # I didn't trigger this command, so ignore the data
#             return
#         
#         self.currCmds.addCmd(
#             cmdr = cmdr,
#             cmdID = cmdID,
#             imObj = imObj,
#             isNewImage = False,
#         )
    
    def doDragStart(self, evt):
        """Mouse down for current drag (whatever that might be).
        """
        if not self.gim.isNormalMode():
            return
        if not self.imDisplayed():
            return
        
        try:
            # this action starts drawing a box to centroid a star,
            # so use the centroid color for a frame
            colorPref = self.typeTagColorPrefDict["c"][1]
            color = colorPref.getValue()
            self.dragStart = self.gim.cnvPosFromEvt(evt)
            self.dragRect = self.gim.cnv.create_rectangle(
                self.dragStart[0], self.dragStart[1], self.dragStart[0], self.dragStart[1],
                outline = color,
                tags = _DragRectTag,
            )
        except Exception:
            self.dragStart = None
            self.dragRect = None
            raise
    
    def doDragContinue(self, evt):
        if not self.gim.isNormalMode():
            return
        if not self.dragStart:
            return

        newPos = self.gim.cnvPosFromEvt(evt)
        self.gim.cnv.coords(self.dragRect, self.dragStart[0], self.dragStart[1], newPos[0], newPos[1])
    
    def doDragEnd(self, evt):
        if not self.gim.isNormalMode():
            return
        if not self.imDisplayed():
            return
        if not self.dragStart:
            return

        endPos = self.gim.cnvPosFromEvt(evt)
        startPos = self.dragStart or endPos

        self.gim.cnv.delete(_DragRectTag)
        self.dragStart = None
        self.dragRect = None
        

        meanPos = numpy.divide(numpy.add(startPos, endPos), 2.0)
        deltaPos = numpy.subtract(endPos, startPos)

        rad = max(deltaPos) / (self.gim.zoomFac * 2.0)
        imPos = self.gim.imPosFromCnvPos(meanPos)
        
        if abs(deltaPos[0]) > 1 and abs(deltaPos[1] > 1):
            # centroid

            # execute centroid command
            cmdStr = "centroid file=%r on=%.2f,%.2f cradius=%.1f" % (self.dispImObj.imageName, imPos[0], imPos[1], rad)
            self.doCmd(cmdStr)
            
        else:
            # select
            self.doSelect(evt)

    def doDS9(self, wdg=None):
        """Display the current image in ds9.
        """
        if not self.imDisplayed():
            self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
            return

        # open ds9 window if necessary
        try:
            if self.ds9Win:
                # reopen window if necessary
                self.ds9Win.doOpen()
            else:
                self.ds9Win = RO.DS9.DS9Win(self.actor)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            self.statusBar.setMsg(RO.StringUtil.strFromException(e), severity = RO.Constants.sevError)
            return
        
        localPath = self.dispImObj.localPath
        self.ds9Win.showFITSFile(localPath)    

    def doEnableCorrection(self, wdg):
        """Enable or disable some kind of correction
        """
        if self.settingEnable:
            return
            
        corrName = wdg["text"].lower()
        if corrName not in ("axes", "focus", "scale"):
            raise RuntimeError("Unknown enable type %s" % (corrName,))
        doEnable = wdg.getBool()
            
        cmdStr = "%s %s" % (corrName, {True: "on", False: "off"}[doEnable])
        self.doCmd(
            cmdStr = cmdStr,
            cmdBtn = wdg,
            cmdSummary = cmdStr,
            failFunc = self._guideEnableCallback,
        )

    def doExpose(self, wdg=None):
        """Take an exposure.
        """
        cmdStr = "on oneExposure " + self.getExpArgStr()
        self.doCmd(
            cmdStr = cmdStr,
            cmdBtn = self.exposeBtn,
            abortCmdStr = "guide off", # is this right?
            cmdSummary = "expose",
        )
        
    def doGuideOff(self, wdg=None):
        """Turn off guiding.
        """
        self.doCmd(
            cmdStr = "guide off",
            cmdBtn = self.guideOffBtn,
        )
    
    def doGuideOn(self, wdg=None):
        """Start guiding.
        """
        try:
            cmdStr = "guide on %s" % self.getGuideArgStr()
        except RuntimeError, e:
            self.statusBar.setMsg(RO.StringUtil.strFromException(e), severity = RO.Constants.sevError)
            self.statusBar.playCmdFailed()
            return
            
        self.doCmd(
            cmdStr = cmdStr,
            cmdBtn = self.guideOnBtn,
            abortCmdStr = "guide off",
            isGuideOn = True,
        )
    
    def doGuideTweak(self, wdg=None):
        """Change guiding parameters.
        """
        try:
            cmdStr = "guide tweak %s" % self.getGuideArgStr(modOnly=True)
        except RuntimeError, e:
            self.statusBar.setMsg(RO.StringUtil.strFromException(e), severity = RO.Constants.sevError)
            self.statusBar.playCmdFailed()
            return
            
        self.doCmd(
            cmdStr = cmdStr,
            cmdBtn = self.applyBtn,
        )
    
    def doMap(self, evt=None):
        """Window has been mapped"""
        if self.dispImObj:
            # give the guide frame a chance to be redrawn so zoom can be set correctly
            self.update_idletasks()
            self.showImage(self.dispImObj)
    
    def doNextIm(self, wdg=None):
        """Show next image from history list"""
        revHist, currInd = self.getHistInfo()
        if currInd == None:
            self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevWarning)
            return

        try:
            nextImName = revHist[currInd-1]
        except IndexError:
            self.statusBar.setMsg("Showing newest image", severity = RO.Constants.sevWarning)
            return
        
        self.showImage(self.imObjDict[nextImName])
    
    def doPrevIm(self, wdg=None):
        """Show previous image from history list"""
        self.showCurrWdg.setBool(False)

        revHist, currInd = self.getHistInfo()
        if currInd == None:
            self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevError)
            return

        try:
            prevImName = revHist[currInd+1]
        except IndexError:
            self.statusBar.setMsg("Showing oldest image", severity = RO.Constants.sevWarning)
            return
        
        self.showImage(self.imObjDict[prevImName])
            
    def doSelect(self, evt):
        """Select a star based on a mouse click
        - If near a found star, select it
        - Otherwise centroid at that point and select the result (if successful)
        """
        if not self.gim.isNormalMode():
            return
        cnvPos = self.gim.cnvPosFromEvt(evt)
        imPos = self.gim.imPosFromCnvPos(cnvPos)

        try:
            # get current image object
            if not self.imDisplayed():
                return
            
            # erase data for now (helps for early return)
            self.dispImObj.selDataColor = None
    
            # look for nearby centroid to choose
            selStarData = None
            minDistSq = _MaxDist
            for typeChar, starDataList in self.dispImObj.starDataDict.iteritems():
                #print "doSelect checking typeChar=%r, nstars=%r" % (typeChar, len(starDataList))
                tag, colorPref = self.typeTagColorPrefDict[typeChar]
                color = colorPref.getValue()
                for starData in starDataList:
                    if None in starData[2:4]:
                        continue
                    distSq = (starData[2] - imPos[0])**2 + (starData[3] - imPos[1])**2
                    if distSq < minDistSq:
                        minDistSq = distSq
                        selStarData = starData
                        selColor = color
    
            if selStarData:
                self.dispImObj.selDataColor = (selStarData, selColor)
        finally:
            # update display
            self.showSelection()
    
    def doShowCurr(self, wdg=None):
        """Handle show current image button"""
        doShowCurr = self.showCurrWdg.getBool()
        
        if doShowCurr:
            sev = RO.Constants.sevNormal
            helpText = "Show new images; click to hold this image"
            self.holdWarnWdg.grid_remove()
#           self.statusBar.setMsg("",
#               severity=RO.Constants.sevNormal,
#           )
        else:
            sev = RO.Constants.sevWarning
            helpText = "Hold this image; click to show new images"
            self.holdWarnWdg.grid()
#           self.statusBar.setMsg("Hold mode: guide controls disabled",
#               severity=RO.Constants.sevWarning,
#           )
        self.showCurrWdg.setSeverity(sev)
        self.showCurrWdg.helpText = helpText
        
        self.enableCmdButtons()
        
        if not doShowCurr:
            return

        # show most recent downloaded image, if any, else most recent image
        revHist = self.imObjDict.values()
        if not revHist:
            return

        for imObj in revHist:
            if imObj.isDone:
                break
        else:
            # display show most recent image
            imObj = revHist[0]
        
        self.showImage(imObj, forceCurr=True)
    
    def doShowHideImage(self, wdg=None):
        """Handle show/hide image button
        """
        doShow = self.showHideImageWdg.getBool()
        if doShow:
            self.gim.grid()
        else:
            self.gim.grid_remove()
    
    def enableCmdButtons(self, wdg=None):
        """Set enable of command buttons.
        """
#        print "enableCmdButtons; self.doingCmd=%s" % (self.doingCmd,)
        showCurrIm = self.showCurrWdg.getBool()
        isImage = self.imDisplayed()
        isCurrIm = isImage and not self.nextImWdg.getEnable()
        isSel = (self.dispImObj != None) and (self.dispImObj.selDataColor != None)
        isGuiding = self.isGuiding()
        isExec = (self.doingCmd != None)
        isExecOrGuiding = isExec or isGuiding
        areParamsModified = self.areParamsModified()
        try:
            self.getGuideArgStr()
            guideCmdOK = True
        except RuntimeError:
            guideCmdOK = False
        if _DebugBtnEnable:
            print "%s GuideWdg: showCurrIm=%s, isImage=%s, isCurrIm=%s, isSel=%s, isGuiding=%s, isExec=%s, isExecOrGuiding=%s, areParamsModified=%s, guideCmdOK=%s" % \
            (self.actor, showCurrIm, isImage, isCurrIm, isSel, isGuiding, isExec, isExecOrGuiding, areParamsModified, guideCmdOK)
        
        self.currentBtn.setEnable(areParamsModified)
        
        self.exposeBtn.setEnable(showCurrIm and not isExecOrGuiding)
        self.centerBtn.setEnable(showCurrIm and isCurrIm and isSel and not isExecOrGuiding)
                
        self.guideOnBtn.setEnable(showCurrIm and guideCmdOK and not isExecOrGuiding)
        
        self.applyBtn.setEnable(showCurrIm and isGuiding and isCurrIm and guideCmdOK and areParamsModified)

        guideState = self.guiderModel.guideState[0]
        gsLower = guideState and guideState.lower()
        self.guideOffBtn.setEnable(gsLower in ("on", "starting"))

        self.cancelBtn.setEnable(isExec)
        self.ds9Btn.setEnable(isImage)
        if (self.doingCmd != None) and (self.doingCmd[1] != None):
            self.doingCmd[1].setEnable(False)
    
    def enableHistButtons(self):
        """Set enable of prev and next buttons"""
        revHist, currInd = self.getHistInfo()
        #print "currInd=%s, len(revHist)=%s, revHist=%s" % (currInd, len(revHist), revHist)
        enablePrev = enableNext = False
        prevGap = nextGap = False
        if (len(revHist) > 0) and (currInd != None):
            prevInd = currInd + 1
            if prevInd < len(revHist):
                enablePrev = True
                if not self.dispImObj.isInSequence:
                    prevGap = True
                elif not (self.imObjDict[revHist[prevInd]]).isInSequence:
                    prevGap = True
                    
            nextInd = currInd - 1
            if not self.showCurrWdg.getBool() and nextInd >= 0:
                enableNext = True
                if not self.dispImObj.isInSequence:
                    nextGap = True
                elif not (self.imObjDict[revHist[nextInd]]).isInSequence:
                    nextGap = True
        
        self.prevImWdg.setState(enablePrev, prevGap)
        self.nextImWdg.setState(enableNext, nextGap)
    
    def fetchCallback(self, imObj):
        """Called when an image is finished downloading.
        """
        if self.dispImObj == imObj:
            # something has changed about the current object; update display
            self.showImage(imObj)
        elif self.showCurrWdg.getBool() and imObj.isDone:
            # a new image is ready; display it
            self.showImage(imObj)
        
        if self.currDownload and self.currDownload.isDone:
            # start downloading next image, if any
            if self.nextDownload:
                self.currDownload = self.nextDownload
                self.nextDownload = None
                if self.currDownload.state == imObj.Ready:
                    # download not already started, so start it already
                    self.currDownload.fetchFile()
            else:
                self.currDownload = None
    
    def getExpArgStr(self, modOnly = False):
        """Return exposure time, bin factor, etc.
        as a string suitable for a guide camera command.
        
        Inputs:
        - inclImgFile: if True, the imgFile argument is included
        - modOnly: if True, only values that are not default are included
        
        The defaults are suitable for autoguiding.
        
        Raise RuntimeError if imgFile wanted but no display image.
        """
        args = ArgList(modOnly)
        
        args.addKeyWdg("expTime", self.expTimeWdg)

        return str(args)
    
    def getGuideArgStr(self, modOnly=False):
        """Return guide command arguments as a string.
        
        Inputs:
        - modOnly: if True, only include values the user has modified
        
        Note: guide mode is always included.
        
        Raise RuntimeError if guiding is not permitted.
        """
        argList = []
        expArgStr = self.getExpArgStr(
            modOnly = modOnly,
        )
        if expArgStr:
            argList.append(expArgStr)
            
        return " ".join(argList)
    
    def getHistInfo(self):
        """Return information about the location of the current image in history.
        Returns:
        - revHist: list of image names in history in reverse order (most recent first)
        - currImInd: index of displayed image in history
          or None if no image is displayed or displayed image not in history at all
        """
        revHist = self.imObjDict.keys()
        if self.dispImObj == None:
            currImInd = None
        else:
            try:
                currImInd = revHist.index(self.dispImObj.imageName)
            except ValueError:
                currImInd = None
        return (revHist, currImInd)
    
    def getSelStarArgs(self, posKey, modOnly=False):
        """Get guide command arguments appropriate for the selected star.
        
        Inputs:
        - posKey: name of star position keyword: one of gstar or centerOn
        - modOnly: if True, only return data if user has selected a different star
        """
        if not self.imDisplayed():
            raise RuntimeError("No image")

        if not self.dispImObj.selDataColor:
            raise RuntimeError("No star selected")
        
        if modOnly and self.dispImObj.defSelDataColor \
            and (self.dispImObj.defSelDataColor[0] == self.dispImObj.selDataColor[0]):
            return ""

        starData = self.dispImObj.selDataColor[0]
        pos = starData[2:4]
        rad = starData[6]
        return "%s=%.2f,%.2f cradius=%.1f" % (posKey, pos[0], pos[1], rad)
    
    def ignoreEvt(self, evt=None):
        pass

    def imDisplayed(self):
        """Return True if an image is being displayed (with data).
        """
        return self.dispImObj and (self.gim.dataArr != None)
    
    def imObjFromKeyVar(self, keyVar):
        """Return imObj that matches keyVar's cmdr and cmdID, or None if none"""
        cmdInfo = self.currCmds.getCmdInfoFromKeyVar(keyVar)
        if not cmdInfo:
            return None
        return cmdInfo.imObj
    
    def isDispObj(self, imObj):
        """Return True if imObj is being displayed, else False"""
        return self.dispImObj and (self.dispImObj.imageName == imObj.imageName)
    
    def isGuiding(self):
        """Return True if guiding"""
        guideState = self.guiderModel.guideState[0]
        if guideState == None:
            return False

        return guideState.lower() != "off"
    
    def redisplayImage(self, *args, **kargs):
        """Redisplay current image"""
        if self.dispImObj:
            self.showImage(self.dispImObj)

    def showImage(self, imObj, forceCurr=None):
        """Display an image.
        Inputs:
        - imObj image to display
        - forceCurr force guide params to be set to current value?
            if None then automatically set based on the Current button
        """
        self.dragStart = None
        self.dragRect = None
        #print "showImage(imObj=%s)" % (imObj,)
        # expire current image if not in history (this should never happen)
        if (self.dispImObj != None) and (self.dispImObj.imageName not in self.imObjDict):
            sys.stderr.write("GuideWdg warning: expiring display image that was not in history")
            self.dispImObj.expire()
        
        fitsIm = imObj.getFITSObj() # note: this sets various useful attributes of imObj
        mask = None
        #print "fitsIm=%s, self.gim.ismapped=%s" % (fitsIm, self.gim.winfo_ismapped())
        if fitsIm:
            self.plateBtn.setEnable(imObj.hasPlateView)        
            showPlateView = imObj.hasPlateView and self.plateBtn.getBool()

            #self.statusBar.setMsg("", RO.Constants.sevNormal)
            if showPlateView:
                imArr = imObj.plateImageArr
                mask = imObj.plateMaskArr
            else:
                imArr = fitsIm[0].data
                if imArr == None:
                    self.gim.showMsg("Image %s has no data in plane 0" % (imObj.imageName,),
                        severity=RO.Constants.sevWarning)
                    return
            
                if len(fitsIm) > 1 and \
                    fitsIm[1].data.shape == imArr.shape and \
                    fitsIm[1].data.dtype == numpy.uint8:
                    mask = fitsIm[1].data

        else:
            if imObj.didFail:
                sev = RO.Constants.sevNormal
            else:
                if (imObj.state == imObj.Ready) and self.gim.winfo_ismapped():
                    # image not downloaded earlier because guide window was hidden at the time
                    # get it now
                    imObj.fetchFile()
                sev = RO.Constants.sevNormal
            self.gim.showMsg(imObj.getStateStr(), sev)
            imArr = None
        
        # display new data
        self.gim.showArr(imArr, mask = mask)
        self.dispImObj = imObj
        self.imNameWdg.set(imObj.imageName)
        self.imNameWdg.xview("end")
        
        # update guide params
        # if looking through the history then force current values to change
        # otherwise leave them alone unless they are already tracking the defaults
        if forceCurr == None:
            forceCurr = not self.showCurrWdg.getBool()

        if forceCurr or self.expTimeWdg.getIsCurrent():
            self.expTimeWdg.set(imObj.expTime)
        self.expTimeWdg.setDefault(imObj.expTime)

        self.enableHistButtons()
        
        if imArr != None:
            pass
            # add existing annotations, if any

    def showSelection(self):
        """Display the current selection.
        """
        # clear current selection
        self.gim.removeAnnotation(_SelTag)

        if not self.dispImObj or not self.dispImObj.selDataColor:
            # disable command buttons accordingly
            self.enableCmdButtons()
            
            # clear data display
            self.starXPosWdg.set(None)
            self.starYPosWdg.set(None)
            self.starFWHMWdg.set(None)
            self.starAmplWdg.set(None)
            self.starBkgndWdg.set(None)
            return
        
        starData, color = self.dispImObj.selDataColor

        # draw selection
        self.gim.addAnnotation(
            GImDisp.ann_X,
            imPos = starData[2:4],
            isImSize = False,
            rad = _SelRad,
            holeRad = _SelHoleRad,
            tags = _SelTag,
            fill = color,
        )
        
        # update data display
        self.starXPosWdg.set(starData[2])
        self.starYPosWdg.set(starData[3])
        fwhm = (starData[8] + starData[9]) / 2.0
        self.starFWHMWdg.set(fwhm)
        self.starAmplWdg.set(starData[14])
        self.starBkgndWdg.set(starData[13])
    
        # enable command buttons accordingly
        self.enableCmdButtons()

    def showStar(self, starData):
        """Display data about a star on the current image."""
        typeChar = starData[0].lower()
        xyPos = starData[2:4]
        rad = starData[6]
        tag, colorPref = self.typeTagColorPrefDict[typeChar]
        color = colorPref.getValue()
        if (None not in xyPos) and (rad != None):
            self.gim.addAnnotation(
                GImDisp.ann_Circle,
                imPos = xyPos,
                rad = rad,
                isImSize = True,
                tags = tag,
                outline = color,
            )
        if typeChar == "g":
            if (None not in xyPos):
                self.gim.addAnnotation(
                    GImDisp.ann_Plus,
                    imPos = starData[2:4],
                    rad = _GuideRad,
                    holeRad = _GuideHoleRad,
                    isImSize = False,
                    tags = tag,
                    fill = color,
                )
            xyPredPos = starData[15:17]
            if None not in xyPredPos:
                self.gim.addAnnotation(
                    GImDisp.ann_Plus,
                    imPos = xyPredPos,
                    rad = _GuidePredPosRad,
                    isImSize = False,
                    tags = tag,
                    fill = color,
                )
    
    def togglePlateView(self, wdg=None):
        """Toggle between normal image view and guide probes on plate view.
        """
        if not self.imDisplayed():
            return
        self.showImage(self.dispImObj)
    
    def _filesCallback(self, keyVar):
        """Handle files files keyVar

        String(help="type; one of: guide, flat, dark..."),
        String(help="base directory for these files (relative to image root)"),
        String(help="name of fully processed image file"),
        String(help="name of mask file"),
        """
#        print "%s _filesCallback(%s); valueList=%s; isCurrent=%s)" % (self.actor, keyVar, keyVar.valueList, keyVar.isCurrent)
        if not keyVar.isCurrent or not keyVar.isGenuine:
            return
            
        fileType, imageDir, imageName = keyVar.valueList[0:3]
        cmdr, cmdID = filesVar.getCmdrCmdID()
        imageName = imageDir + imageName

        # create new object data
        localBaseDir = self.guiderModel.ftpSaveToPref.getValue()
        imObj = GuideImage.GuideImage(
            localBaseDir = localBaseDir,
            imageName = imageName,
            downloadWdg = self.guiderModel.downloadWdg,
            fetchCallFunc = self.fetchCallback,
        )
        self._trackMem(imObj, str(imObj))
        self.addImToHist(imObj)
        
        if self.gim.winfo_ismapped():
            if not self.currDownload:
                # nothing being downloaded, start downloading this image
                self.currDownload = imObj
                imObj.fetchFile()
                if (self.dispImObj == None or self.dispImObj.didFail) and self.showCurrWdg.getBool():
                    # nothing already showing so display the "downloading" message for this image
                    self.showImage(imObj)
            else:
                # queue this up to be downloaded (replacing any image already there)
                self.nextDownload = imObj
        elif self.showCurrWdg.getBool():
            self.showImage(imObj)
        
        # create command info
        self.currCmds.addCmd(
            cmdr = cmdr,
            cmdID = cmdID,
            imObj = imObj,
            isNewImage = True,
        )

        # purge excess images
        if self.dispImObj:
            dispImName = self.dispImObj.imageName
        else:
            dispImName = ()
        isNewest = True
        if len(self.imObjDict) > self.nToSave:
            keys = self.imObjDict.keys()
            for imName in keys[self.nToSave:]:
                if imName == dispImName:
                    if not isNewest:
                        self.imObjDict[imName].isInSequence = False
                    continue
                if _DebugMem:
                    print "Purging %r from history" % (imName,)
                purgeImObj = self.imObjDict.pop(imName)
                purgeImObj.expire()
                isNewest = False
        self.enableHistButtons()
    
    def _expStateCallback(self, keyVar):
        """exposure state has changed.
        
        values are is:
        - user name
        - exposure state string (e.g. flushing, reading...)
        - start timestamp
        - remaining time for this state (sec; 0 or None if short or unknown)
        - total time for this state (sec; 0 or None if short or unknown)
        """
        if not keyVar.isCurrent:
            self.expStateWdg.setNotCurrent()
            return

        expStateStr, startTime, remTime, netTime = keyVar.valueList
        lowState = expStateStr.lower()
        remTime = remTime or 0.0 # change None to 0.0
        netTime = netTime or 0.0 # change None to 0.0

        if lowState == "paused":
            errState = RO.Constants.sevWarning
        else:
            errState = RO.Constants.sevNormal
        self.expStateWdg.set(expStateStr, severity = errState)
        
        if not keyVar.isGenuine:
            # data is cached; don't mess with the countdown timer
            return
        
        exposing = lowState in ("integrating", "resume")
        
        if netTime > 0:
            # print "starting a timer; remTime = %r, netTime = %r" % (remTime, netTime)
            # handle a countdown timer
            # it should be stationary if expStateStr = paused,
            # else it should count down
            if lowState in ("integrating", "resume"):
                # count up exposure
                self.expTimer.start(
                    value = netTime - remTime,
                    newMax = netTime,
                    countUp = True,
                )
            elif lowState == "paused":
                # pause an exposure with the specified time remaining
                self.expTimer.pause(
                    value = netTime - remTime,
                )
            else:
                # count down anything else
                self.expTimer.start(
                    value = remTime,
                    newMax = netTime,
                    countUp = False,
                )
            self.expTimer.grid()
        else:
            # hide countdown timer
            self.expTimer.grid_remove()
            self.expTimer.clear()
        
#        if self.exposing in (True, False) \
#            and self.exposing != exposing \
#            and self.winfo_ismapped():
#            if exposing:
#                TUI.PlaySound.exposureBegins()
#            else:
#                TUI.PlaySound.exposureEnds()
        
        self.exposing = exposing

    def _guideEnableCallback(self, dum=None):
        """guideEnable callback

        Key("guideEnable",
            Enum(False, True, name="axis", help="move azimuth, altitude and rotation to correct pointing"),
            Enum(False, True, name="focus", help="move the secondary mirror to correct focus"),
            Enum(False, True, name="scale", help="move the primary and secondary mirrors to correct plate scale"),
            help="Which guiding corrections are enabled",
        ),
        """
        keyVar = self.guiderModel.guideEnable
        isCurrent = keyVar.isCurrent
        self.settingEnable = True
        try:
            self.axesEnableWdg.set(keyVar[0], isCurrent)
            self.focusEnableWdg.set(keyVar[1], isCurrent)
            self.scaleEnableWdg.set(keyVar[2], isCurrent)
        finally:
            self.settingEnable = False

    def _guideStateCallback(self, keyVar):
        """Guide state callback
        """
        guideState = keyVar[0]
        self.guideStateWdg.set(guideState, isCurrent=keyVar.isCurrent)

        if not keyVar.isCurrent:
            return

        # handle disable of guide on button when guiding starts
        # (unlike other commands, "guide on" doesn't actually end until guiding terminates!)
        if self.doingCmd and self.doingCmd[2]:
            gsLower = guideState and guideState.lower()
            if gsLower != "off":
                self.doingCmd = None
        self.enableCmdButtons()

    def updMaskColor(self, *args, **kargs):
        """Handle new mask color preference"""
        for ind in range(len(self.maskColorPrefs)):
            self.gim.maskInfo[ind].setColor(self.maskColorPrefs[ind].getValue())
        self.redisplayImage()
    
    def _exitHandler(self):
        """Delete all image files
        """
        for imObj in self.imObjDict.itervalues():
            imObj.expire()

class ArgList(object):
    def __init__(self, modOnly):
        self.argList = []
        self.modOnly = modOnly
    
    def addArg(self, arg):
        """Add argument: arg
        modOnly is ignored.
        """
        self.argList.append(arg)

    def addKeyWdg(self, key, wdg):
        """Add argument: key=wdg.getString()
        If modOnly=True then the item is omitted if default.
        """
        if self.modOnly and wdg.isDefault():
            return
        strVal = wdg.getString()
        if strVal:
            self.argList.append("=".join((key, wdg.getString())))
    
    def addWdg(self, wdg):
        """If modOnly=True then the item is omitted if default.
        """
        if not self.modOnly or not wdg.isDefault():
            self.argList.append(wdg.getString())
    
    def __str__(self):
        return " ".join(self.argList)

if __name__ == "__main__":
    import GuideTest
    #import gc
    #gc.set_debug(gc.DEBUG_SAVEALL) # or gc.DEBUG_LEAK to print lots of messages

    root = GuideTest.tuiModel.tkRoot

    GuideTest.init("guider")

    testFrame = GuideWdg(root)
    testFrame.pack(expand="yes", fill="both")
    testFrame.wait_visibility() # must be visible to download images
    GuideTest.setParams(expTime=5, mode="field")

#   GuideTest.runDownload(
#       basePath = "dcam/UT060404/",
#       imPrefix = "proc-d",
#       startNum = 101,
#       numImages = 2,
#       waitMs = 2500,
#   )
#   testFrame.doChooseIm()
#   testFrame.showFITSFile("/Users/rowen/test.fits")

    root.mainloop()
