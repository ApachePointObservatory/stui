#!/usr/bin/env python
"""Guiding support

To do: use the main X to stop user-supplied corrections and get rid of the extra X widget.

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
                    Added _DebugWdgEnable to help diagnose button enable errors.
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
2009-09-14 ROwen    Many fixes and cleanups. Added gcamera exposure state.
2009-10-29 ROwen    Added guide star position error vector annotations to plate view.
                    Changed default for Plate checkbutton to True.
2009-11-04 ROwen    Added annotations to plate view: probe number, scale and N/E axes.
2009-11-05 ROwen    Added X annotation to plate view to indicate disabled probes.
                    Modified to send downloaded image to FocusPlot.
                    Modified for updated GuideImage that does not parse or store plate view information.
                    Handle unknown guide star position error by not drawing a vector.
2009-11-06 ROwen    Show failure to make plate view as a message on the status bar.
                    Bug fix: could refer to pointingErr when it is not defined.
2009-11-07 ROwen    Modified to download new images if either this window or the focus plot are mapped.
2009-11-12 ROwen    Added widets to show the applied correction. Still need to allow applying corrections.
                    Added widgets to enable and disable guide probes; however these are not yet displayed
                    due to ticket 433: Please fix gprobeBits so it includes the "enabled" bit.
2009-11-13 ROwen    Increased RA/Dec/Rot correction display resolution from 0.1" to 0.01".
2010-01-25 ROwen    Added simulation info.
2010-02-18 ROwen    Fixed the test code.
2010-03-12 ROwen    Changed to use Models.getModel.
2010-06-26 ROwen    Fix ticket 920: sent "guide on" instead of "on" to turn on guiding.
2010-06-28 ROwen    Fixed invalid variable reference in _guideStateCallback (thanks to pychecker).
2010-08-25 ROwen    Display enable/disable controls.
                    Modified to use fullGProbeBits (a temporary addition to the guider model
                    to avoid having to use the gprobes keyword directly).
2010-09-27 ROwen    Increased size of probe images in the plate image: changed relSize from 0.8 to 0.5.
                    Improved positioning of probe number labels.
2010-10-18 ROwen    Fix ticket 1097: sending wrong commands to enable and disable guide probes.
2010-11-19 ROwen    Moved CorrWdg and CmdInfo to separate modules.
2010-11-20 ROwen    Bug fix: removed an obsolete callback that was causing a traceback.
2011-01-18 ROwen    Added Center Up button.
2011-04-01 ROwen    Stop sending "plot display=..." as part of the guide on command. It's no longer useful.
2011-06-13 ROwen    Moved guide state code to a separate GuideStateWdg widget.
2011-06-17 ROwen    Added support for refraction balance ratio guide parameter.
                    Modified Exp Time to show time from the guider, not the displayed image.
                    Modified to allow applying guide parameter changes even when guiding is off.
2011-08-29 ROwen    Bug fix: command buttons were not in the correct state if guideState=failed.
2012-07-10 ROwen    Removed use of update_idletasks.
2012-10-31 ROwen    Removed use of guider keyword refractionWavelengths, since it is never output.
2012-11-14 ROwen    Stop using Checkbutton indicatoron=False; it is no longer supported on MacOS X.
                    Removed unused, invisible image show/hide control.
2013-03-21 ROwen    Modified to use guider keyword gprobeBits instead of synthetic keyword fullGProbeBits
                    now that ticket #433 is fixed!
2013-03-25 ROwen    Added support for the Stack parameter.
                    Added +/- suffix to guide probe number to indicate above/below focus.
2013-03-26 ROwen    Put exposure time and related controls all on the same line, to save space.
2013-03-27 ROwen    Bug fix: +/- suffix was separated from probe number.
                    Bug fix: on MacOS X the last probe's name might be hidden (a TkAqua bug).
2013-03-28 ROwen    Fix ticket #1765: error when attempting to disable a fiber.
2013-03-28 ROwen    Add +/- suffix to probe name labels in guide images.
2013-04-01 ROwen    Add guide probe name annotation to unassembled (non-plate) image.
2013-05-13 ROwen    Support older guide images that don't have gprobebits information.
2013-05-17 ROwen    Bug fix: plateInfo and havePlateInfo might be referenced without being defined.
2015-09-18 ROwen    Add support for gzipped FITS files to the "Choose..." button, as per SDSS ticket 2430.
                    Note that tkFileDialog.askopenfilename does not support file types that contain
                    more than one dot, such as '.fits.gz' (at least on MacOS), so I had to use ".gz"
                    and permit any gzipped file.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
2015-11-05 ROwen    Modernized "except" syntax.
"""
import atexit
import os
import re
import sys
import traceback
import weakref
import Tkinter
import tkFileDialog
import numpy
import opscore.actor
from opscore.utility import assembleImage
import RO.Alg
import RO.CanvasUtil
import RO.Constants
import RO.DS9
import RO.MathUtil
import RO.OS
import RO.Prefs
import RO.StringUtil
from RO.TkUtil import Timer
import RO.Wdg
import RO.Wdg.GrayImageDispWdg as GImDisp

import TUI.Base.Wdg
import TUI.Models
import TUI.TUIMenu.DownloadsWindow
from . import CmdInfo
from . import CorrWdg
from . import FocusPlotWindow
from . import GuideImage
from . import GuideStateWdg
from . import MangaDitherWdg

_HelpPrefix = "Instruments/Guiding/index.html#"

_MaxDist = 15
_CentroidTag = "centroid"
_FindTag = "findStar"
_GuideTag = "guide"
_SelTag = "showSelection"
_DragRectTag = "centroidDrag"
_BoreTag = "boresight"
_ErrTag = "poserr"
_ProbeNumTag = "probeNum"

_SelRad = 18
_SelHoleRad = 9
_BoreRad = 6
_GuideRad = 18
_GuideHoleRad = 9
_GuidePredPosRad = 9

_HistLen = 100

_DebugMem = False # print a message when a file is deleted from disk?
_DebugWdgEnable = False # print messages that help debug widget enable?

_AboveFocusStr = "+" # u"\N{UPWARDS ARROW}"
_BelowFocusStr = "-" # u"\N{DOWNWARDS ARROW}"

ErrPixPerArcSec = 40 # pixels per arcsec of error on the plug plate

DisabledProbeXSizeFactor = 1.0

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
    OffStates = frozenset(("off", "failed"))
    def __init__(self,
        master,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)
        
        self.actor = "guider"
        self.guiderModel = TUI.Models.getModel("guider")
        self.tuiModel = TUI.Models.getModel("tui")
        self.dragStart = None
        self.dragRect = None
        self.currDownload = None # image object being downloaded
        self.nextDownload = None # next image object to download
        self.settingProbeEnableWdg = False
        self.currCmdInfoList = []
        self.focusPlotTL = None
        self.plateViewAssembler = assembleImage.AssembleImage(relSize=0.5)
        
        self.ftpSaveToPref = self.tuiModel.prefs.getPrefVar("Save To")
        downloadTL = self.tuiModel.tlSet.getToplevel(TUI.TUIMenu.DownloadsWindow.WindowName)
        self.downloadWdg = downloadTL and downloadTL.getWdg()
        
        # color prefs
        def getColorPref(prefName, defColor, isMask = False):
            """Get a color preference. If not found, make one."""
            pref = self.tuiModel.prefs.getPrefVar(prefName, None)
            if pref is None:
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
        
        self._btnsLaidOut = False
        
        totCols = 20
        
        row=0

        guideStateWdg = GuideStateWdg.GuideStateWdg(
            master = self,
            helpURL = _HelpPrefix + "GuidingStatus",
        )
        guideStateWdg.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1

        helpURL = _HelpPrefix + "HistoryControls"
        
        histFrame = Tkinter.Frame(self)
        
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
            helpURL = _HelpPrefix + "ImageDisplay",
            defRange = "99.5%",
        )
        self.plateBtn = RO.Wdg.Checkbutton(
            master = self.gim.toolFrame,
            text = "Plate",
            defValue = True,
            callFunc = self.togglePlateView,
            helpText = "Show plate view of guide probes or normal image",
        )
        self.plateBtn.pack(side="left")
        self.gim.grid(row=row, column=0, columnspan=totCols, sticky="news")
        self.grid_rowconfigure(row, weight=1)
        self.grid_columnconfigure(totCols - 1, weight=1)
        row += 1
        
        self.defCnvCursor = self.gim.cnv["cursor"]
        
        helpURL = _HelpPrefix + "ImageAndStarData"
        
        starFrame = Tkinter.Frame(self)

        RO.Wdg.StrLabel(
            master = starFrame,
            text = " Star ",
            bd = 0,
            padx = 0,
            helpText = "Information about the selected star",
            helpURL = helpURL,
        ).pack(side="left")
        
        RO.Wdg.StrLabel(
            master = starFrame,
            text = "Pos: ",
            bd = 0,
            padx = 0,
            helpText = "Centroid of the selected star (pix)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starXPosWdg = RO.Wdg.FloatLabel(
            master = starFrame,
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
            master = starFrame,
            text = ", ",
            bd = 0,
            padx = 0,
        ).pack(side="left")
        self.starYPosWdg = RO.Wdg.FloatLabel(
            master = starFrame,
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
            master = starFrame,
            text = "  FWHM: ",
            bd = 0,
            padx = 0,
            helpText = "FWHM of selected star (pix)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starFWHMWdg = RO.Wdg.FloatLabel(
            master = starFrame,
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
            master = starFrame,
            text = "  Ampl: ",
            bd = 0,
            padx = 0,
            helpText = "Amplitude of selected star (ADUs)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starAmplWdg = RO.Wdg.FloatLabel(
            master = starFrame,
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
            master = starFrame,
            text = "  Bkgnd: ",
            bd = 0,
            padx = 0,
            helpText = "Background level at selected star (ADUs)",
            helpURL = helpURL,
        ).pack(side="left")
        self.starBkgndWdg = RO.Wdg.FloatLabel(
            master = starFrame,
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

        Tkinter.Frame(self, height=2, bg="dark gray").grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1
        
        paramFrame = Tkinter.Frame(self)

        helpURL = _HelpPrefix + "GuidingParameters"

        helpText = "exposure time"
        RO.Wdg.StrLabel(
            master = paramFrame,
            text = "Exp Time",
            helpText = helpText,
            helpURL = helpURL,
        ).pack(side="left")
        
        self.expTimeWdg = RO.Wdg.FloatEntry(
            paramFrame,
            label = "Exp Time",
            minValue = 0.0,
            defValue = 5.0,
            defFormat = "%.1f",
            defMenu = "Current",
            minMenu = "Minimum",
            autoIsCurrent = True,
            width = 5,
            helpText = helpText,
            helpURL = helpURL,
        )
        self.expTimeWdg.pack(side="left")

        RO.Wdg.StrLabel(
            master = paramFrame,
            text = "sec",
            anchor = "w",
        ).pack(side="left")

        Tkinter.Frame(master = paramFrame, width=15).pack(side="left")

        helpText = "number of exposures to stack"
        RO.Wdg.StrLabel(
            master = paramFrame,
            text = "Stack",
            helpText = helpText,
            helpURL = helpURL,
        ).pack(side="left")
        
        self.stackWdg = RO.Wdg.IntEntry(
            paramFrame,
            label = "Stack",
            minValue = 1,
            defValue = 1,
            defMenu = "Current",
            minMenu = "Minimum",
            autoIsCurrent = True,
            width = 2,
            helpText = helpText,
            helpURL = helpURL,
        )
        self.stackWdg.pack(side="left")

        Tkinter.Frame(master = paramFrame, width=15).pack(side="left")

        helpText = "refraction balance; approx. 0 for BOSS, 1 for APOGEE"
        RO.Wdg.StrLabel(
            master = paramFrame,
            text = "Refr. Balance",
            helpText = helpText,
            helpURL = helpURL,
        ).pack(side="left")

        self.refBalanceWdg = RO.Wdg.FloatEntry(
            paramFrame,
            label = "Refr. Balance",
            defValue = 1.0,
            defFormat = "%.1f",
            defMenu = "Current",
            width = 5,
            autoIsCurrent = True,
            helpText = helpText,
            helpURL = helpURL,
        )
        self.refBalanceWdg.pack(side="left")
        
        Tkinter.Frame(master = paramFrame, width=15).pack(side="left")
       
        self.applyBtn = RO.Wdg.Button(
            master = paramFrame,
            text = "Apply",
            callFunc = self.doChangeParams,
            helpText = "Apply new guide parameters",
            helpURL = helpURL,
        )
        self.applyBtn.pack(side="left")

        self.currentBtn = RO.Wdg.Button(
            master = paramFrame,
            text = "Current",
            command = self.doRevertParams,
            helpText = "Restore current guide parameters",
            helpURL = helpURL,
        )
        self.currentBtn.pack(side="left")
        
        paramFrame.grid(row=row, column=0, columnspan=totCols, sticky="w")
        row += 1

        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
            helpURL = _HelpPrefix + "StatusBar",
        )
        
        Tkinter.Frame(self, height=2, bg="dark gray").grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1

        self.mangaDitherWdg = MangaDitherWdg.MangaDitherWdg(
            master = self,
            helpURL = helpURL,
        )
        self.mangaDitherWdg.grid(row=row, column=0, columnspan=totCols, sticky="w")
        row += 1

        Tkinter.Frame(self, height=2, bg="dark gray").grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1

        self.corrWdg = CorrWdg.CorrWdg(
            master = self,
            doCmdFunc = self.doCmd,
            statusBar = self.statusBar,
            helpURL = helpURL,
        )
        
        self.corrWdg.grid(row=row, column=0, columnspan=totCols, sticky="w")
        row += 1
        
        Tkinter.Frame(self, height=2, bg="dark gray").grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1

        RO.Wdg.StrLabel(
            master = self,
            text = "Probe",
        ).grid(row=row, column=0)
        
        self.enableProbeWdgSet = []

        self.enableProbeFrame = Tkinter.Frame(self)
        self.enableProbeFrame.grid(row=row, column=1, columnspan=totCols-3, sticky="w")
        
        self.enableAllProbesWdg = RO.Wdg.Button(
            master = self,
            text = "All",
            callFunc = self.doEnableAllProbes,
            helpText = "enable all available guide probes",
        )
        self.enableAllProbesWdg.grid(row=row, column=totCols-2, sticky="e")
        row+= 1


        self.guideParamWdgSet = [
            self.expTimeWdg,
            self.stackWdg,
            self.refBalanceWdg,
        ]
        for wdg in self.guideParamWdgSet:
            wdg.addCallback(self.enableCmdButtons)

        self.devSpecificFrame = Tkinter.Frame(self)
        self.devSpecificFrame.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1

        self.statusBar.grid(row=row, column=0, columnspan=totCols, sticky="ew")
        row += 1
        
        helpURL = _HelpPrefix + "GuidingControls"
        
        cmdButtonFrame = Tkinter.Frame(self)
        self.exposeBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Expose",
            callFunc = self.doExpose,
            helpText = "Take an exposure",
            helpURL = helpURL,
        )
        
        self.centerUpBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Center Up",
            callFunc = self.doCenterUp,
            helpText = "Center up on current image",
            helpURL = helpURL,
        )
        
        self.guideOnBtn = RO.Wdg.Button(
            cmdButtonFrame,
            text = "Guide",
            callFunc = self.doGuideOn,
            helpText = "Start guiding",
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
        self.centerUpBtn.grid(row=0, column=col)
        col += 1
        self.guideOnBtn.grid(row=0, column=col)
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

#        self.gim.cnv.bind("<Button-1>", self.doDragStart, add=True)
#        self.gim.cnv.bind("<B1-Motion>", self.doDragContinue, add=True)
#        self.gim.cnv.bind("<ButtonRelease-1>", self.doDragEnd, add=True)
        
        # keyword variable bindings
        self.guiderModel.stack.addCallback(self._stackCallback)
        self.guiderModel.expTime.addCallback(self._expTimeCallback)
        self.guiderModel.file.addCallback(self._fileCallback)
        self.guiderModel.gprobeBits.addCallback(self._gprobeBitsCallback)
        self.guiderModel.guideState.addCallback(self._guideStateCallback)
        self.guiderModel.refractionBalance.addCallback(self._refractionBalanceCallback)

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
            print("GuideWdg deleting %s" % (objName,))
            del(self._memDebugDict[objID])

        self._memDebugDict[objID] = weakref.ref(obj, refGone)
        del(obj)

    def addImToHist(self, imObj, ind=None):
        imageName = imObj.imageName
        if ind is None:
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
        """Cancel outstanding commands.
        """
        if _DebugWdgEnable:
            print("cmdCancel(); self.currCmdInfoList=%s" % (self.currCmdInfoList,))
        if not self.currCmdInfoList:
            return
        for cmdInfo in self.currCmdInfoList[:]:
            cmdInfo.cmdVar.abort()

    def cmdCallback(self, cmdVar=None):
        """Use this callback when launching a command that is saved in self.currCmdInfoList
        
        DO NOT use as the sole means of re-enabling guide on button(s)
        because if guiding turns on successfully, the command is not reported
        as done until guiding is terminated.
        """
        if _DebugWdgEnable:
            print("cmdCallback(cmdVar=%s); self.currCmdInfoList=%s" % (cmdVar, self.currCmdInfoList,))
        didChange = False
        for cmdInfo in self.currCmdInfoList[:]:
            if cmdInfo.cmdVar.isDone:
                if _DebugWdgEnable:
                    print("Removing %s from currCmdInfoList" % (cmdInfo,))
                didChange = True
                self.currCmdInfoList.remove(cmdInfo)
        if didChange:
            self.enableCmdButtons()

    def cursorNormal(self, evt=None):
        """Show normal image cursor and reset control-click if present
        """
        self.gim.cnv["cursor"] = self.defCnvCursor

    def doChooseIm(self, wdg=None):
        """Choose an image to display.
        """
        self.showCurrWdg.setBool(False)

        if self.dispImObj is not None:
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
        if startDir is not None and os.path.isdir(startDir):
            kargs["initialdir"] = startDir
            if startFile is not None and os.path.isfile(os.path.join(startDir, startFile)):
                kargs["initialfile"] = startFile

        imPath = tkFileDialog.askopenfilename(
            filetypes = [("FITS", (".fit", ".fits", ".gz"))],
        **kargs)
        if not imPath:
            return
            
        self.showFITSFile(imPath)
    
    def doRevertParams(self, wdg=None):
        """Restore default value of all guide parameter widgets"""
        for wdg in self.guideParamWdgSet:
            wdg.restoreDefault()
        
        if self.dispImObj and self.dispImObj.defSelDataColor and self.dispImObj.selDataColor \
            and (self.dispImObj.defSelDataColor[0] != self.dispImObj.selDataColor[0]):
            # star selection has changed
            self.dispImObj.selDataColor = self.dispImObj.defSelDataColor
            self.showSelection()
        
    def doCenterUp(self, wdg=None):
        """Center on current exposure (guide loop must be running).
        """
        cmdStr = "centerUp"
        self.doCmd(
            cmdStr = cmdStr,
            wdg = self.centerUpBtn,
            abortCmdStr = None,
        )

    def doChangeParams(self, wdg=None):
        """Change guide parameters.
        """
        cmdStrSet = []
        try:
            if not (self.expTimeWdg.getIsCurrent() and self.stackWdg.getIsCurrent()):
                cmdStrSet.append("setExpTime time=%s stack=%s" % (self.expTimeWdg.getString(), self.stackWdg.getString()))
            if not self.refBalanceWdg.getIsCurrent():
                cmdStrSet.append("setRefractionBalance corrRatio=%s" % (self.refBalanceWdg.getString(),))
        except RuntimeError as e:
            self.statusBar.setMsg(RO.StringUtil.strFromException(e), severity = RO.Constants.sevError)
            self.statusBar.playCmdFailed()
            return
        
        for cmdStr in cmdStrSet:
            self.doCmd(
                cmdStr = cmdStr,
                wdg = self.applyBtn,
            )
        
    def doCmd(self,
        cmdStr,
        wdg = None,
        isGuideOn = False,
        actor = None,
        abortCmdStr = None,
        cmdSummary = None,
        failFunc = None,
    ):
        """Execute a command.
        Inputs:
        - cmdStr        the command to execute
        - wdg           the widget that triggered the command; when command finishes, widget is enabled
        - isGuideOn     set True for commands that start guiding
        - actor         the actor to which to send the command;
                        defaults to the actor for the guide camera
        - abortCmdStr   abort command, if any
        - cmdSummary    command summary for the status bar
        - failFunc      function to execute if the command fails or is cancelled
        
        Returns the cmdVar (so you can add callbacks to it).
        """
        actor = actor or self.actor
        for cmdInfo in self.currCmdInfoList:
            if cmdInfo.cmdVar.cmdStr == cmdStr and cmdInfo.cmdVar.actor == actor:
                raise RuntimeError("This command is already active")
        cmdVar = opscore.actor.CmdVar(
            actor = actor,
            cmdStr = cmdStr,
            abortCmdStr = abortCmdStr,
        )
        cmdInfo = CmdInfo.CmdInfo(
            cmdVar = cmdVar,
            isGuideOn = isGuideOn,
            wdg = wdg,
            doneFunc = self.cmdCallback,
            failFunc = failFunc,
        )
        self.currCmdInfoList.append(cmdInfo)
        self.enableCmdButtons()
        self.statusBar.doCmd(cmdVar, cmdSummary)
        
        return cmdVar
    
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
        except Exception as e:
            self.statusBar.setMsg(RO.StringUtil.strFromException(e), severity = RO.Constants.sevError)
            return
        
        localPath = self.dispImObj.localPath
        self.ds9Win.showFITSFile(localPath)    

    def doEnableProbe(self, wdg):
        """Enable or disable a guide probe named by wdg["text"]
        """
        if self.settingProbeEnableWdg:
            return

        probeName = re.search("\d+", wdg["text"]).group()
        doEnable = wdg.getBool()
        cmdStr = "%s fibers=%s" % ({True: "enable", False: "disable"}[doEnable], probeName)
        self.doCmd(
            cmdStr = cmdStr,
            wdg = wdg,
            cmdSummary = cmdStr,
            failFunc = self._gprobeBitsCallback,
        )

    def doEnableAllProbes(self, dum=None):
        """Enable all available guide probes
        """
        if self.settingProbeEnableWdg:
            return

        probeNameList = []
        for ind, gprobeBits in enumerate(self.guiderModel.gprobeBits):
            if gprobeBits & 0x03 != 0:
                continue
            self.enableProbeWdgSet[ind].setEnable(False)
            probeNameList.append(str(ind+1))
        if not probeNameList:
            return

        cmdStr = "enable fibers=%s" % (",".join(probeNameList))
        self.doCmd(
            cmdStr = cmdStr,
            wdg = self.enableAllProbesWdg,
            cmdSummary = "enable all available probes",
            failFunc = self._gprobeBitsCallback,
        )
        
    def doExpose(self, wdg=None):
        """Take an exposure.
        """
        cmdStr = "on oneExposure time=%s" % (self.expTimeWdg.getString(),)
        self.doCmd(
            cmdStr = cmdStr,
            wdg = self.exposeBtn,
            abortCmdStr = "off",
        )
        
    def doGuideOff(self, wdg=None):
        """Turn off guiding.
        """
        self.doCmd(
            cmdStr = "off",
            wdg = self.guideOffBtn,
        )
    
    def doGuideOn(self, wdg=None):
        """Start guiding.
        """
        try:
            cmdStr = "on time=%s" % (self.expTimeWdg.getString(),)
        except RuntimeError as e:
            self.statusBar.setMsg(RO.StringUtil.strFromException(e), severity = RO.Constants.sevError)
            self.statusBar.playCmdFailed()
            return
            
        self.doCmd(
            cmdStr = cmdStr,
            wdg = self.guideOnBtn,
            abortCmdStr = "off",
            isGuideOn = True,
        )
    
    def doMap(self, evt=None):
        """Window has been mapped"""
        if self.dispImObj:
            # give the guide frame a chance to be redrawn so zoom can be set correctly.
            # formerly this was done using update_idletasks followed by calling showImage directly;
            # I'm not sure how to reproduce the problem so I'm not sure any workaround
            # is still needed and if this particular one does the job.
            Timer(0.001, self.showImage, self.dispImObj)
    
    def doNextIm(self, wdg=None):
        """Show next image from history list"""
        revHist, currInd = self.getHistInfo()
        if currInd is None:
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
        if currInd is None:
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
            for typeChar, starDataList in self.dispImObj.starDataDict.items():
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
        revHist = list(self.imObjDict.values())
        if not revHist:
            return

        for imObj in revHist:
            if imObj.isDone:
                break
        else:
            # display show most recent image
            imObj = revHist[0]
        
        self.showImage(imObj, forceCurr=True)
    
    def enableCmdButtons(self, wdg=None):
        """Set enable of command buttons.
        """
#        print "enableCmdButtons; self.currCmdInfoList=%s" % (self.currCmdInfoList,)
        showCurrIm = self.showCurrWdg.getBool()
        isImage = self.imDisplayed()
        isCurrIm = isImage and not self.nextImWdg.getEnable()
        isSel = (self.dispImObj is not None) and (self.dispImObj.selDataColor is not None)
        isGuiding = self.isGuiding()
        isExec = bool(self.currCmdInfoList)
        isExecOrGuiding = isExec or isGuiding
        areParamsModified = self.areParamsModified()
        try:
            self.expTimeWdg.getString()
            guideCmdOK = True
        except RuntimeError:
            guideCmdOK = False
        if _DebugWdgEnable:
            print("%s GuideWdg: showCurrIm=%s, isImage=%s, isCurrIm=%s, isSel=%s, isGuiding=%s, isExec=%s, isExecOrGuiding=%s, areParamsModified=%s, guideCmdOK=%s" % \
            (self.actor, showCurrIm, isImage, isCurrIm, isSel, isGuiding, isExec, isExecOrGuiding, areParamsModified, guideCmdOK))
        
        self.applyBtn.setEnable(areParamsModified)
        self.currentBtn.setEnable(areParamsModified)
        
        self.exposeBtn.setEnable(showCurrIm and not isExecOrGuiding)
        
        self.centerUpBtn.setEnable(showCurrIm and isGuiding)
                
        self.guideOnBtn.setEnable(showCurrIm and guideCmdOK and not isExecOrGuiding)

        guideState = self.guiderModel.guideState[0]
        gsLower = guideState and guideState.lower()
        self.guideOffBtn.setEnable(gsLower in ("on", "starting"))

        self.cancelBtn.setEnable(isExec)
        self.ds9Btn.setEnable(isImage)
        
        self._enableEnableAllProbesWdg()
    
    def _enableEnableAllProbesWdg(self):
        """Enable or disable the enableAllProbesWdg as appropriate
        """
        enableEnableAllProbesWdg = False
        if self.enableAllProbesWdg not in (cmdInfo.wdg for cmdInfo in self.currCmdInfoList):
            for ind, gprobeBits in enumerate(self.guiderModel.gprobeBits):
                if gprobeBits & 0x03 != 0:
                    continue
                if gprobeBits & 0x04 == 0:
                    enableEnableAllProbesWdg = True
                    break
        self.enableAllProbesWdg.setEnable(enableEnableAllProbesWdg)        
    
    def enableHistButtons(self):
        """Set enable of prev and next buttons"""
        revHist, currInd = self.getHistInfo()
        #print "currInd=%s, len(revHist)=%s, revHist=%s" % (currInd, len(revHist), revHist)
        enablePrev = enableNext = False
        prevGap = nextGap = False
        if (len(revHist) > 0) and (currInd is not None):
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
#        print "fetchCallback(imObj=%s); imObj.state=%s" % (imObj, imObj.state)
        if self.dispImObj == imObj:
            # something has changed about the current object; update display
            self.showImage(imObj)
        elif self.showCurrWdg.getBool() and imObj.isDone:
            # a new image is ready; display it
            self.showImage(imObj)
        
        if not imObj.isDone:
            return
        
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
        
        # display focus plot (or clear it if info not available)
        if self.focusPlotTL:
            self.focusPlotTL.getWdg().plot(imObj)
    
    def getHistInfo(self):
        """Return information about the location of the current image in history.
        Returns:
        - revHist: list of image names in history in reverse order (most recent first)
        - currImInd: index of displayed image in history
          or None if no image is displayed or displayed image not in history at all
        """
        revHist = list(self.imObjDict.keys())
        if self.dispImObj is None:
            currImInd = None
        else:
            try:
                currImInd = revHist.index(self.dispImObj.imageName)
            except ValueError:
                currImInd = None
        return (revHist, currImInd)
    
    def imDisplayed(self):
        """Return True if an image is being displayed (with data).
        """
        return self.dispImObj and (self.gim.dataArr is not None)
    
    def isDispObj(self, imObj):
        """Return True if imObj is being displayed, else False"""
        return self.dispImObj and (self.dispImObj.imageName == imObj.imageName)
    
    def isGuiding(self):
        """Return True if guiding"""
        guideState = self.guiderModel.guideState[0]
        if guideState is None:
            return False

        return guideState.lower() not in self.OffStates
    
    def redisplayImage(self, *args, **kargs):
        """Redisplay current image"""
        if self.dispImObj:
            self.showImage(self.dispImObj)
    
    def showFITSFile(self, imPath):
        """Display a FITS file.
        """     
        # try to find image in history
        # using samefile is safer than trying to match paths as strings
        # (RO.OS.expandPath *might* be thorough enough to allow that,
        # but no promises and one would have to expand every path being checked)
        for imObj in self.imObjDict.values():
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
        if startDir is not None:
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
        if self.dispImObj is not None:
            try:
                ind = self.imObjDict.index(self.dispImObj.imageName)
            except KeyError:
                pass
        self.addImToHist(imObj, ind)
        self.showImage(imObj)

    def showImage(self, imObj, forceCurr=None):
        """Display an image.
        Inputs:
        - imObj image to display
        - forceCurr force guide params to be set to current value?
            if None then automatically set based on the Current button
        """
#        print "showImage(imObj=%s, forceCurr=%s)" % (imObj, forceCurr)
        errSevMsgList = [] # list of (severity, error messages) to print to status bar
        self.dragStart = None
        self.dragRect = None
        #print "showImage(imObj=%s)" % (imObj,)
        # expire current image if not in history (this should never happen)
        if (self.dispImObj is not None) and (self.dispImObj.imageName not in self.imObjDict):
            sys.stderr.write("GuideWdg warning: expiring display image that was not in history")
            self.dispImObj.expire()
        
        fitsIm = imObj.getFITSObj() # note: this sets various useful attributes of imObj
        mask = None
#        print "fitsIm=%s, self.gim.ismapped=%s" % (fitsIm, self.gim.winfo_ismapped())
        isPlateView = False
        plateInfo = None
        havePlateInfo = False
        if fitsIm:
            try:
                plateInfo = self.plateViewAssembler(fitsIm)
            except assembleImage.NoPlateInfo:
                if self.plateBtn.getBool():
                    errSevMsgList.append((RO.Constants.sevWarning, "No plate view: not a guider image"))
            except assembleImage.AIException as e:
                errSevMsgList.append(
                    (RO.Constants.sevWarning, "No plate view: %s" % (RO.StringUtil.strFromException(e),))
                )
            except Exception as e:
                errSevMsgList.append(
                    (RO.Constants.sevError, "No plate view: %s" % (RO.StringUtil.strFromException(e),))
                )
                sys.stderr.write("Could not assemble plate view of %r:\n" % (imObj.localPath,))
                traceback.print_exc(file=sys.stderr)
            havePlateInfo = plateInfo is not None

            self.plateBtn.setEnable(havePlateInfo)        
            showPlateView = havePlateInfo and self.plateBtn.getBool()

            #self.statusBar.setMsg("", RO.Constants.sevNormal)
            if showPlateView:
                imArr = plateInfo.plateImageArr
                mask = plateInfo.plateMaskArr
                isPlateView = True
            else:
                imArr = fitsIm[0].data
                if imArr is None:
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
        
        self.enableHistButtons()
        
        if isPlateView:
            # add plate annotations
            for stampInfo in plateInfo.stampList:
                doPutProbeLabelOnRight = True
                if stampInfo.gpEnabled:
                    # add vector showing star position error, if known
                    if numpy.alltrue(numpy.isfinite(stampInfo.starRADecErrArcSec)):
                        pointingErr = stampInfo.starRADecErrArcSec
                        if pointingErr[0] >= 0:
                            doPutProbeLabelOnRight = False
                        pointingErrRTheta = RO.MathUtil.rThetaFromXY(pointingErr * (1, -1))
                        annRadius = pointingErrRTheta[0] * ErrPixPerArcSec
        #                print "add annotation at %s of radius %0.1f" % (stampInfo.decImCtrPos, annRadius)
                        self.gim.addAnnotation(
                            GImDisp.ann_Line,
                            imPos = stampInfo.decImCtrPos,
                            isImSize = False,
                            rad = annRadius,
                            angle = pointingErrRTheta[1],
                            tags = _ErrTag,
                            fill = "green",
                        )
                        
                        # show uncertainty of position error? how? Also the info isn't available yet.
                else:
                    # put an X through the image
                    self.gim.addAnnotation(
                        GImDisp.ann_X,
                        imPos = stampInfo.decImCtrPos,
                        isImSize = True,
                        rad = stampInfo.getRadius() * DisabledProbeXSizeFactor,
                        tags = _ErrTag,
                        fill = "red",
                    )

                # add text label showing guide probe number
                probeName = makeGProbeName(stampInfo.gpNumber, stampInfo.gpBits)
                boxWidth = stampInfo.image.shape[0] / 2.0
                if doPutProbeLabelOnRight:
                    anchor = "w"
                    textPos = stampInfo.decImCtrPos + (boxWidth + 3, 0)
                else:
                    anchor = "e"
                    textPos = stampInfo.decImCtrPos - (boxWidth + 1, 0)
#                 print "num=%s; startPos=%s; ctrPos=%s; boxWidth=%s; textPos=%s" % \
#                     (stampInfo.gpNumber, stampInfo.decImStartPos, stampInfo.decImCtrPos, boxWidth, textPos)
                self.gim.addAnnotation(
                    GImDisp.ann_Text,
                    imPos = textPos,
                    text = probeName,
                    rad = 10,
                    anchor = anchor,
                    isImSize = False,
                    tags = _ProbeNumTag,
                    fill = "green",
                )
                
            # add N/E axis
            axisLength = 25
            axisMargin = 20
            boxSize = axisLength + axisMargin
            axisImPos = self.gim.imPosFromArrIJ(numpy.array(imArr.shape) - 1)
            self.gim.addAnnotation(
                GImDisp.ann_Line,
                imPos = axisImPos,
                cnvOffset = (-boxSize, boxSize),
                rad = axisLength,
                angle = 0,
                isImSize = False,
                tags = _ProbeNumTag,
                fill = "green",
                arrow = "last",
            )
            self.gim.addAnnotation(
                GImDisp.ann_Text,
                text = "E",
                imPos = axisImPos,
                cnvOffset = (3-axisMargin, boxSize),
                rad = 10,
                anchor = "w",
                isImSize = False,
                tags = _ProbeNumTag,
                fill = "green",
            )

            self.gim.addAnnotation(
                GImDisp.ann_Line,
                imPos = axisImPos,
                cnvOffset = (-boxSize, boxSize),
                rad = axisLength,
                angle = -90,
                isImSize = False,
                tags = _ProbeNumTag,
                fill = "green",
                arrow = "last",
            )
            self.gim.addAnnotation(
                GImDisp.ann_Text,
                text = "N",
                imPos = axisImPos,
                cnvOffset = (-boxSize, axisMargin),
                rad = 10,
                anchor = "s",
                isImSize = False,
                tags = _ProbeNumTag,
                fill = "green",
            )

            # add scale
            scaleCnvOffset = numpy.array((10, 20))
            scaleLength = ErrPixPerArcSec
            scaleImPos = self.gim.imPosFromCnvPos((0, 0))
            self.gim.addAnnotation(
                GImDisp.ann_Line,
                imPos = scaleImPos,
                cnvOffset = scaleCnvOffset,
                rad = scaleLength,
                angle = 0,
                isImSize = False,
                tags = _ErrTag,
                fill = "green",
            )
            self.gim.addAnnotation(
                GImDisp.ann_Text,
                text = "1 arcsec",
                imPos = scaleImPos,
                cnvOffset = scaleCnvOffset,
                anchor = "sw",
                rad = 10,
                isImSize = False,
                tags = _ErrTag,
                fill = "green",
            )
        elif havePlateInfo:
            # add probe names as annotation to the unassembled image
            for stampInfo in plateInfo.stampList:
                doPutProbeLabelOnRight = True
                if not stampInfo.gpEnabled:
                    # put an X through the image
                    self.gim.addAnnotation(
                        GImDisp.ann_X,
                        imPos = stampInfo.gpCtr,
                        isImSize = True,
                        rad = stampInfo.getRadius() * DisabledProbeXSizeFactor,
                        tags = _ErrTag,
                        fill = "red",
                    )

                # add text label showing guide probe number
                probeName = makeGProbeName(stampInfo.gpNumber, stampInfo.gpBits)
                boxWidth = stampInfo.image.shape[0] / 2.0
                if doPutProbeLabelOnRight:
                    anchor = "w"
                    textPos = stampInfo.gpCtr + (boxWidth + 3, 0)
                else:
                    anchor = "e"
                    textPos = stampInfo.gpCtr - (boxWidth + 1, 0)
#                 print "num=%s; startPos=%s; ctrPos=%s; boxWidth=%s; textPos=%s" % \
#                     (stampInfo.gpNumber, stampInfo.decImStartPos, stampInfo.decImCtrPos, boxWidth, textPos)
                self.gim.addAnnotation(
                    GImDisp.ann_Text,
                    imPos = textPos,
                    text = probeName,
                    rad = 10,
                    anchor = anchor,
                    isImSize = False,
                    tags = _ProbeNumTag,
                    fill = "green",
                )

        if errSevMsgList:
            errSevMsgList.sort()
            severity, errMsg = errSevMsgList[-1] 
            self.statusBar.setMsg(errMsg, severity=severity, isTemp=True)
        else:
            self.statusBar.clearTempMsg()

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

    def togglePlateView(self, wdg=None):
        """Toggle between normal image view and guide probes on plate view.
        """
        if not self.imDisplayed():
            return
        self.showImage(self.dispImObj)
    
    def _fileCallback(self, keyVar):
        """Handle file files keyVar

        String(help="base directory for these files (relative to image root)"),
        String(help="name of fully processed image file"),
        """
#        print "%s _fileCallback(%s); valueList=%s; isCurrent=%s)" % (self.actor, keyVar, keyVar.valueList, keyVar.isCurrent)
        if not keyVar.isCurrent or not keyVar.isGenuine:
            return
        if not self.focusPlotTL:
            self.focusPlotTL = self.tuiModel.tlSet.getToplevel(FocusPlotWindow.WindowName)
            
        imageDir, imageName = keyVar.valueList[0:2]
        if imageDir[-1] != "/" and imageName[0] != "/":
            print("Warning: hacked around broken guider.files keyword")
            imageName = imageDir + "/" + imageName
        else:
            imageName = imageDir + imageName
            

        # create new object data
        localBaseDir = self.ftpSaveToPref.getValue()
        imObj = GuideImage.GuideImage(
            localBaseDir = localBaseDir,
            imageName = imageName,
            downloadWdg = self.downloadWdg,
            fetchCallFunc = self.fetchCallback,
        )
        self._trackMem(imObj, str(imObj))
        self.addImToHist(imObj)
        
        if self.gim.winfo_ismapped() or (self.focusPlotTL and self.focusPlotTL.getVisible()):
            if not self.currDownload:
                # nothing being downloaded, start downloading this image
                self.currDownload = imObj
                imObj.fetchFile()
                if (self.dispImObj is None or self.dispImObj.didFail) and self.showCurrWdg.getBool():
                    # nothing already showing so display the "downloading" message for this image
                    self.showImage(imObj)
            else:
                # queue this up to be downloaded (replacing any image already there)
                self.nextDownload = imObj
        elif self.showCurrWdg.getBool():
            self.showImage(imObj)
        
        # purge excess images
        if self.dispImObj:
            dispImName = self.dispImObj.imageName
        else:
            dispImName = ()
        isNewest = True
        if len(self.imObjDict) > self.nToSave:
            keys = list(self.imObjDict.keys())
            for imName in keys[self.nToSave:]:
                if imName == dispImName:
                    if not isNewest:
                        self.imObjDict[imName].isInSequence = False
                    continue
                if _DebugMem:
                    print("Purging %r from history" % (imName,))
                purgeImObj = self.imObjDict.pop(imName)
                purgeImObj.expire()
                isNewest = False
        self.enableHistButtons()
    
    def _guideStateCallback(self, keyVar):
        """Guide state callback
        """
        if not keyVar.isCurrent:
            return

        # handle disable of guide on button when guiding starts
        # (unlike other commands, "on" doesn't actually end until guiding terminates!)
        for cmdInfo in self.currCmdInfoList[:]:
            if cmdInfo.isGuideOn and not cmdInfo.cmdVar.isDone:
                gsLower = keyVar[0] and keyVar[0].lower()
                if gsLower != "off":
                    cmdInfo.removeCallbacks(enableWdg=True)
                    self.currCmdInfoList.remove(cmdInfo)
        self.enableCmdButtons()

    def _gprobeBitsCallback(self, dum=None):
        """Guide probe bits callback
        """
        keyVar = self.guiderModel.gprobeBits
        if None in keyVar[:]:
            return

        numProbes = len(keyVar[:])
        numExtraProbes = numProbes - len(self.enableProbeWdgSet)
        if numExtraProbes != self.enableProbeWdgSet:
            for wdg in self.enableProbeWdgSet:
                wdg.grid_forget()
            self.enableProbeWdgSet = []
            row1Len = (numProbes + 1) / 2
            row2Len = numProbes - row1Len
            colList = list(range(row1Len)) + list(range(row2Len))
            rowList = [0]*row1Len + [1]*row2Len
            for ind, bits in enumerate(keyVar):
                probeName = makeGProbeName(ind + 1, bits)
                wdg = RO.Wdg.Checkbutton(
                    master = self.enableProbeFrame,
                    text = probeName,
                    width = len(probeName), # fix display bug on TkAqua
                    callFunc = self.doEnableProbe,
                )
                wdg.grid(row=rowList[ind], column=colList[ind], sticky="w")
                self.enableProbeWdgSet.append(wdg)

        try:
            self.settingProbeEnableWdg = True
            for ind, wdg in enumerate(self.enableProbeWdgSet):
                stateWord = keyVar[ind]
                
                probeAvailable = stateWord & 0x03 == 0
                wdg.setEnable(probeAvailable)

                probeEnabled = probeAvailable and (stateWord & 0x04 == 0)
                wdg.set(probeEnabled)

                if probeAvailable:
                    helpText = "enable or disable this guide probe"
                else:
                    if stateWord & 0x01 != 0:
                        helpText = "guide probe broken"
                    else:
                        helpText = "guide probe not used for this pointing"
                wdg.helpText = helpText
        finally:
            self.settingProbeEnableWdg = False
        self._enableEnableAllProbesWdg()
    
    def _stackCallback(self, keyVar):
        """stack keyword callback
        """
        if keyVar[0] is None:
            return
        
        self.stackWdg.setDefault(keyVar[0])
    
    def _expTimeCallback(self, keyVar):
        """expTime keyword callback
        """
        if keyVar[0] is None:
            return

        self.expTimeWdg.setDefault(keyVar[0])

    def _refractionBalanceCallback(self, keyVar):
        """refractionBalance keyword callback
        """
        if keyVar[0] is None:
            return

        self.refBalanceWdg.setDefault(keyVar[0])    
    
    def updMaskColor(self, *args, **kargs):
        """Handle new mask color preference"""
        for ind in range(len(self.maskColorPrefs)):
            self.gim.maskInfo[ind].setColor(self.maskColorPrefs[ind].getValue())
        self.redisplayImage()
    
    def _exitHandler(self):
        """Delete all image files
        """
        for imObj in self.imObjDict.values():
            imObj.expire()

def makeGProbeName(gprobeNum, gprobeBits):
    """Construct a guide probe name from its number and gProbeBits
    
    Inputs:
    gprobeNum: guide probe number (an integer, though a string will do)
    gprobeBits: guide probe bits; if None then the above/below focus suffix is not added
    """
    if gprobeBits is None:
        suffixStr = ""
    elif gprobeBits & 1<<3 != 0:
        suffixStr = _AboveFocusStr
    elif gprobeBits & 1<<4 != 0:
        suffixStr = _BelowFocusStr
    else:
        suffixStr = ""
    return str(gprobeNum) + suffixStr


if __name__ == "__main__":
    from . import GuideTest
    #import gc
    #gc.set_debug(gc.DEBUG_SAVEALL) # or gc.DEBUG_LEAK to print lots of messages

    root = GuideTest.tuiModel.tkRoot

    testFrame = GuideWdg(root)
    testFrame.pack(expand="yes", fill="both")
    testFrame.wait_visibility() # must be visible to download images
    
    GuideTest.start()

    GuideTest.tuiModel.reactor.run()
