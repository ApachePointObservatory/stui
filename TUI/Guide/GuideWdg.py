#!/usr/local/bin/python
"""Guiding support

To do:
- Update status bar if viewing an image that changes:
  - From going from downloaded to loaded; show the image
  even if showCurr not checked.
  - From downloading to failed: show error message!

- Debug memory leak. But keep current history handling if possible:
  - if viewing oldest image, < > links break or change
    such that the user has a chance to not leave the image
    but image does NOT vanish on its own.

- If lost in history, then bring up a message saying:
	"lost; press < to go to oldest image, > to go to current image"

- Add debugging mode that downloads images from APO
  
- Arrange buttons in two rows
  or only show buttons that are appropriate?
  (i.e. no need to show start guide and stop guide at the same time
  but don't rename buttons as state changes--too easy to click wrong thing)
- Test and clean up manual guiding. I really think the loop is going to
  have to be in the hub, but if not:
  - how do I notify users I'm manually guiding?
  - how do I sensibly  handle halting manual vs auto guiding?
    I don't want 2 buttons for this, but I also want to do the right thing reliably.
	Maybe change "Guide Stop" to "Man Guide Stop"?
  
- Check: if a users presses Expose while guiding what happens?
  We want the user to see their image and not be overwhelmed with
  other images, so I think it should be shown even if "Current"
  is unchecked. Question: do we uncheck "Current" when Expose is pressed?
  I think NOT unless users demand it; it's more transparent that way.

- Add boresight display
- Add predicted star position display and/or...
- Add some kind of display of what guide correction was made;
  preferably a graph that shows a history of guide corrections
  perhaps as a series of linked(?) lines, with older ones dimmer until fade out?
- Add slit display
- Add snap points for dragging along slit -- a big job
- Add ability to see masked data and mask
- Work with Craig to handle "expired" images better.
  These are images that can no longer be used for guiding
  because the telescope has moved.
- Use color prefs for markers
- Add preference to limit # of images saved to disk.
  Include an option to keep images on quit or ask, or always just delete?


History:
2005-02-10 ROwen	alpha version; lots of work to do
2005-02-22 ROwen	Added drag to centroid. Modified for GryImageDispWdg 2005-02-22.
2005-02-23 ROwen	Added exposure time; first cut at setting exp time and thresh when a new image comes in.
2005-03-28 ROwen	Modified for improved files and star keywords.
2005-03-31 ROwen	Implemented hub commands. Added display of current image name.
2005-04-11 ROwen	Modified for GCamModel->GuideModel
2005-04-12 ROwen	Added display of data about selected star.
					Improved to run in normal mode by default and local mode during tests.
2005-04-13 ROwen	Added Stop Guiding and Guide On Boresight.
					Bug fix: mis-handled star data when multiple images used the same (cmdr,cmdID).
2005-04-15 ROwen	Modified to set exposure time and bin factor from the fits image header.
					Modified to send exposure time and bin factor in commands that expose.
					Bug fix: displayed new annotations on the wrong image while the new image was downloading.
2005-04-18 ROwen	Modified to only download guide images if this widget is visible.
					Modified to delete images from disk when they fall off the history list
					or when the application exits (but not in local test mode).
					Initial default exposure time and bin factor are now set from the model.
					Modified to use updated test code.
2005-04-21 ROwen	Added control-click to center on a point and removed the center Button.
					Most errors now write to the status bar (imageRoot unknown is still an exception).
2005-04-26 ROwen	Added preliminary history navigation; it needs some cleanup.
					Added attribute "deviceSpecificFrame" for device-specific controls.
2005-04-27 ROwen	Finished logic for history controls.
					Finished error handling in BasicImObj.
2005-05-13 ROwen	Added preliminary support for manual guiding.
					Re-added the Center button.
					Added references to html help.
					Mod. to pack the widgets instead of gridding them.
					Added _DebugMem flag and commented out the remaining
					non-flag-protected diagnostic print statement.
2005-05-20 ROwen	Bug fix: was not setting ImObj.defThresh on creation.
					But fix: set ImObj.currThresh to None instead of default if curr thresh unknown.
					Bug fix: layout was messed up by going to the packer so reverted to gridder.
					(The space for multiple widgets with expand=True is always shared
					even if some of them only grow in one direction. Truly hideous!)
					Bug fix: the history controls were always disabled.
2005-05-23 ROwen	Mod. to overwrite image files if new ones come in with the same name;
					this simplifies debugging and corrects bugs associated with the old way
					(the new image's ImObj would replace the old one, so the old one
					was never accessible and never deleted).
					Bug fix: typo in code that handled displaying unavailable images.
2005-05-26 ROwen	Cleaned up button enable/disable.
					Added doCmd method to centralize command execution.
2005-06-09 ROwen	Added more _DebugMem output.
					Apparently fixed a bug that prevented file delete for too-old files.
2005-06-10 ROwen	Modified for noStarsFound->noGuideStar in guide model.
					Also changed the no stars message to "Star Not Found".
2005-06-13 ROwen	Bug fix: one of the delete delete messages was mis-formatted.
					Added more memory tracking code.
					Modified test code to download images from APO.
"""
import atexit
import os
import sys
import weakref
import Tkinter
import tkFileDialog
import numarray as num
import pyfits
import RO.Alg
import RO.CanvasUtil
import RO.Constants
import RO.Comm.FTPGet as FTPGet
import RO.DS9
import RO.KeyVariable
import RO.OS
import RO.ScriptRunner
import RO.Wdg
import RO.Wdg.GrayImageDispWdg as GImDisp
import TUI.TUIModel
import GuideModel
import GuideTest

_HelpPrefix = "Guiding/index.html#"

_MaxDist = 15
_CentroidTag = "centroid"
_FindTag = "findStar"
_GuideTag = "guide"
_SelTag = "showSelection"
_DragRectTag = "centroidDrag"
_MarkRad = 15
_HoleRad = 3

_HistLen = 100

# set these via color prefs, eventually
_FindColor = "green"
_CentroidColor = "cyan"
_GuideColor = "red"

_TypeTagColorDict = {
	"c": (_CentroidTag, _CentroidColor),
	"f": (_FindTag, _FindColor),
#	"g": (_GuideTag, _GuideColor),
}

_LocalMode = False # leave false here; change in test code that imports this module if required
_DebugMem = False # print a message when a file is deleted from disk?

#_ImSt_Ready = "ready to download"
#_ImSt_Downloading = "downloading"
#_ImSt_Downloaded = "downloaded"
#_ImSt_FileReadFailed = "cannot read file"
#_ImSt_DownloadFailed = "download failed"
#_ImSt_Expired = "expired; file deleted"

class BasicImObj(object):
	StReady = "ready to download"
	StDownloading = "downloading"
	StDownloaded = "downloaded"
	StFileReadFailed = "cannot read file"
	StDownloadFailed = "download failed"
	StExpired = "expired; file deleted"

	def __init__(self,
		baseDir,
		imageName,
		guideModel,
		fetchCallFunc = None,
		isLocal = False,
	):
		self.baseDir = baseDir
		self.imageName = imageName
		self.maskObj = None
		self.guideModel = guideModel
		self.state = self.StReady
		self.exception = None
		self.fetchCallFunc = fetchCallFunc
		self.isLocal = isLocal or _LocalMode
	
	def didFail(self):
		"""Return False if download failed or image expired"""
		return self.state in (
			self.StFileReadFailed,
			self.StDownloadFailed,
			self.StExpired,
		)

	def isDone(self):
		"""Return True if image file available"""
		return self.state == self.StDownloaded

	def fetchFile(self):
		"""Start downloading the file."""
		if self.isLocal:
			self.state = self.StDownloaded
			self._doCallback()
			return

		(host, rootDir), isCurr = self.guideModel.imageRoot.get()
		if None in (host, rootDir):
			self.state = self.StDownloadFailed
			self.exception = "server info (imageRoot) not yet known"
			self._doCallback()
			return

		self.state = self.StDownloading

		# do NOT use os.path to join remote host path components;
		# simply concatenate instead
		fromPath = rootDir + self.imageName

		toPath = self.getLocalPath()
		
		self.guideModel.ftpLogWdg.getFile(
			host = host,
			fromPath = fromPath,
			toPath = toPath,
			isBinary = True,
			overwrite = True,
			createDir = True,
			callFunc = self._fetchCallFunc,
			dispStr = self.imageName,
			username = "images",
			password = "7nights."
		)
	
	def getFITSObj(self):
		"""If the file is available, return a pyfits object,
		else return None.
		"""
		if self.state == self.StDownloaded:
			try:
				return pyfits.open(self.getLocalPath())
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				self.state = self.StFileReadFailed
				self.exception = e
		return None
	
	def getLocalPath(self):
		"""Return the full local path to the image."""
		return os.path.join(self.baseDir, self.imageName)
	
	def getStateStr(self):
		"""Return a string describing the current state."""
		if self.exception:
			return "%s: %s" % (self.state, self.exception)
		return self.state

	def _fetchCallFunc(self, ftpGet):
		"""Called while an image is being downloaded.
		When the download finishes, handle it.
		"""
		if not ftpGet.isDone():
			return
		ftpState = ftpGet.getState()
		if ftpState == FTPGet.Done:
			self.state = self.StDownloaded
		else:
			self.state = self.StDownloadFailed
			self.exception = ftpGet.getException()
			print "%s download failed: %s" % (self, self.exception)
		self._doCallback()
	
	def _doCallback(self):
		if self.fetchCallFunc:
			self.fetchCallFunc(self)
		if self.isDone():
			self.fetchCallFunc = None
	
	def expire(self):
		"""Delete the file from disk and set state to expired.
		"""
		self.maskObj = None
		if self.isLocal:
			if _DebugMem:
				print "Would delete %r, but is local" % (self.imageName,)
			return
		if self.state == self.StDownloaded:
			self.state = self.StExpired
			locPath = self.getLocalPath()
			if os.path.exists(locPath):
				if _DebugMem:
					print "Deleting %r" % (locPath,)
				os.remove(locPath)
			elif _DebugMem:
				print "Would delete %r, but not found on disk" % (self.imageName,)
		elif _DebugMem:
			print "Would delete %r, but state = %r is not 'downloaded'" % (self.imageName, self.state,)
	
	def __str__(self):
		return "%s(%s)" % (self.__class__.__name__, self.imageName)


class ImObj(BasicImObj):
	def __init__(self,
		baseDir,
		imageName,
		cmdChar,
		cmdr,
		cmdID,
		guideModel,
		fetchCallFunc = None,
		defRadMult = None,
		defThresh = None,
		isLocal = False,
	):
		self.currCmdChar = cmdChar
		self.currCmdrCmdID = (cmdr, cmdID)
		self.sawStarTypes = []
		self.starDataDict = {}
		self.selDataColor = None
		self.defRadMult = defRadMult
		self.defThresh = defThresh
		self.currRadMult = None
		self.currThresh = None

		BasicImObj.__init__(self,
			baseDir = baseDir,
			imageName = imageName,
			guideModel = guideModel,
			fetchCallFunc = fetchCallFunc,
			isLocal = isLocal,
		)
		
	
class GuideWdg(Tkinter.Frame):
	def __init__(self,
		master,
		actor,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		self.actor = actor
		self.guideModel = GuideModel.getModel(actor)
		self.tuiModel = TUI.TUIModel.getModel()
		
		self.nToSave = _HistLen # eventually allow user to set?
		self.imObjDict = RO.Alg.ReverseOrderedDict()
		self._memDebugDict = {}
		self.maskDict = weakref.WeakValueDictionary() # dictionary of mask name: weak link to imObj data for that mask
		self.dispImObj = None # object data for most recently taken image, or None
		self.inCtrlClick = False
		self.ds9Win = None
		
		self.manGuideScriptRunner = None

		row=0

		guideStateFrame = Tkinter.Frame(self)
		
		RO.Wdg.StrLabel(
			master = guideStateFrame,
			text = "Guiding",
		).pack(side="left")
		self.guideStateWdg = RO.Wdg.StrLabel(
			master = guideStateFrame,
			formatFunc = str.capitalize,
			helpText = "Current state of guiding",
			helpURL = _HelpPrefix + "GuidingStatus",
		)
		self.guideStateWdg.pack(side="left")
		
		guideStateFrame.grid(row=row, column=0, sticky="ew")
		row += 1
		
		helpURL = _HelpPrefix + "HistoryControls"
		
		histFrame = Tkinter.Frame(self)
		
		self.prevImWdg = RO.Wdg.Button(
			histFrame,
			text = u"\N{WHITE LEFT-POINTING TRIANGLE}",
			callFunc = self.doPrevIm,
			helpText = "Show previous image",
			helpURL = helpURL,
		)
		self.prevImWdg.pack(side="left")
		
		self.nextImWdg = RO.Wdg.Button(
			histFrame,
			text = u"\N{WHITE RIGHT-POINTING TRIANGLE}",
			callFunc = self.doNextIm,
			helpText = "Show next image",
			helpURL = helpURL,
		)
		self.nextImWdg.pack(side="left")
		
		self.showCurrWdg = RO.Wdg.Checkbutton(
			histFrame,
			text = "Current",
			defValue = True,
			callFunc = self.doShowCurr,
			helpText = "Display current image?",
			helpURL = helpURL,
		)
		self.showCurrWdg.pack(side="left")
		
		self.imNameWdg = RO.Wdg.StrLabel(
			master = histFrame,
			anchor="e",
			helpText = "Name of displayed image",
			helpURL = helpURL,
			)
		self.imNameWdg.pack(side="left", expand=True, fill="x", padx=4)
		
		self.chooseImWdg = RO.Wdg.Button(
			histFrame,
			text = "Choose...",
			callFunc = self.doChooseIm,
			helpText = "Choose a fits file to display",
			helpURL = helpURL,
		)
		self.chooseImWdg.pack(side="left")
		
		histFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		self.gim = GImDisp.GrayImageWdg(self, helpURL = _HelpPrefix + "Image")
		self.gim.grid(row=row, column=0, sticky="news")
		self.grid_rowconfigure(row, weight=1)
		self.grid_columnconfigure(0, weight=1)
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
			helpText = "FWHM of selected star (ADUs)",
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

		starFrame.grid(row=row, column=0, sticky="ew")
		row += 1
		
		helpURL = _HelpPrefix + "AcquisitionControls"
		
		inputFrame = Tkinter.Frame(self)

		helpText = "exposure time"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Exp Time",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.expTimeWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = self.guideModel.gcamInfo.minExpTime,
			maxValue = self.guideModel.gcamInfo.maxExpTime,
			defValue = self.guideModel.gcamInfo.defExpTime,
			defFormat = "%.1f",
			defMenu = "Current",
			minMenu = "Minimum",
			autoIsCurrent = True,
			helpText = helpText,
			helpURL = helpURL,
		)
		self.expTimeWdg.pack(side="left")

		RO.Wdg.StrLabel(
			inputFrame,
			text = "sec",
			width = 4,
			anchor = "w",
		).pack(side="left")

		helpText = "binning factor"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Bin",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.binFacWdg = RO.Wdg.IntEntry(
			inputFrame,
			minValue = 1,
			maxValue = 99,
			defValue = self.guideModel.gcamInfo.defBinFac,
			defMenu = "Current",
			autoIsCurrent = True,
			helpText = helpText,
		)
		self.binFacWdg.pack(side="left")
		
		helpText = "threshold for finding stars"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Thresh",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.threshWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = 0,
			defValue = 3.0, # set from hub, once we can!!!
			defFormat = "%.1f",
			defMenu = "Current",
			autoIsCurrent = True,
			width = 5,
			helpText = helpText,
			helpURL = helpURL,
		)
		self.threshWdg.pack(side="left")

		RO.Wdg.StrLabel(
			inputFrame,
			text = u"\N{GREEK SMALL LETTER SIGMA}",
		).pack(side="left")
		
		helpText = "radius multipler for finding stars"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "RadMult",
			helpText = helpText,
			helpURL = helpURL,
		).pack(side="left")
		
		self.radMultWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = 0.5,
			defValue = 1.0, # set from hub, once we can!!!
			defFormat = "%.1f",
			defMenu = "Current",
			autoIsCurrent = True,
			width = 5,
			helpText = helpText,
			helpURL = helpURL,
		)
		self.radMultWdg.pack(side="left")

		inputFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		self.devSpecificFrame = Tkinter.Frame(self)
		self.devSpecificFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			dispatcher = self.tuiModel.dispatcher,
			prefs = self.tuiModel.prefs,
			playCmdSounds = True,
			helpURL = _HelpPrefix + "StatusBar",
		)
		self.statusBar.grid(row=row, column=0, sticky="ew")
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
		self.exposeBtn.pack(side="left")
		
		self.centerBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Center",
			callFunc = self.doCenterOnSel,
			helpText = "Put selected star on the boresight",
			helpURL = helpURL,
		)
		if self.guideModel.gcamInfo.slitViewer:
			self.centerBtn.pack(side="left")
		
		self.manGuideBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Man Guide",
			callFunc = self.doManGuide,
			helpText = "Expose repeatedly; use ctrl-click to center",
			helpURL = helpURL,
		)
		if self.guideModel.gcamInfo.slitViewer:
			self.manGuideBtn.pack(side="left")

		self.guideOnBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Guide",
			callFunc = self.doGuideOn,
			helpText = "Start guiding on selected star",
			helpURL = helpURL,
		)
		self.guideOnBtn.pack(side="left")
		
		self.guideOnBoresightBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Guide Boresight",
			callFunc = self.doGuideOnBoresight,
			helpText = "Guide on whatever is at the boresight",
			helpURL = helpURL,
		)
		if self.guideModel.gcamInfo.slitViewer:
			self.guideOnBoresightBtn.pack(side="left")
		
		self.guideOffBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Stop Guiding",
			callFunc = self.doGuideOff,
			helpText = "Turn off guiding",
			helpURL = helpURL,
		)
		self.guideOffBtn.pack(side="left")
		
		# leave room for the resize control
		Tkinter.Label(cmdButtonFrame, text=" ").pack(side="right")
		
		self.ds9Btn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "DS9",
			callFunc = self.doDS9,
			helpText = "Display image in ds9",
			helpURL = helpURL,
		)
		self.ds9Btn.pack(side="right")

		cmdButtonFrame.grid(row=row, column=0, sticky="ew")
		row += 1
		
		# enable controls accordingly
		self.enableCmdBtns()
		self.enableHistBtns()
		
		# event bindings
		self.gim.cnv.bind("<Button-1>", self.dragStart, add=True)
		self.gim.cnv.bind("<B1-Motion>", self.dragContinue, add=True)
		self.gim.cnv.bind("<ButtonRelease-1>", self.dragEnd, add=True)
		self.gim.cnv.bind("<Control-Button-1>", self.doCenterOnClick)
		
		self.threshWdg.bind("<FocusOut>", self.doFindStars)
		self.threshWdg.bind("<Return>", self.doFindStars)
		self.radMultWdg.bind("<FocusOut>", self.doFindStars)
		self.radMultWdg.bind("<Return>", self.doFindStars)
		
		# keyword variable bindings
		self.guideModel.fsActRadMult.addIndexedCallback(self.updRadMult)
		self.guideModel.fsActThresh.addIndexedCallback(self.updThresh)
		self.guideModel.files.addCallback(self.updFiles)
		self.guideModel.star.addCallback(self.updStar)
		self.guideModel.guiding.addCallback(self.updGuiding)
		self.guideModel.starQuality.addIndexedCallback(self.updStarQuality)
		self.guideModel.noGuideStar.addCallback(self.updNoGuideStar)

		# bindings to set the image cursor
		tl = self.winfo_toplevel()
		tl.bind("<Control-KeyPress>", self.cursorCtr, add=True)
		tl.bind("<Control-KeyRelease>", self.ignoreEvt, add=True)
		tl.bind("<KeyRelease>", self.cursorNormal, add=True)
		
		# exit handler
		atexit.register(self._exitHandler)

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

	def cursorCtr(self, evt=None):
		"""Show image cursor for "center on this point".
		"""
		self.gim.cnv["cursor"] = "crosshair"
	
	def cursorNormal(self, evt=None):
		"""Show normal image cursor.
		"""
		self.gim.cnv["cursor"] = self.defCnvCursor
	
	def doCenterOnClick(self, evt):
		"""Center up on the command-clicked image location.
		"""
		self.inCtrlClick = True
		
		if not self.dispImObj:
			self.statusBar.setMsg("Ctrl-click requires an image", severity = RO.Constants.sevError)
			self.statusBar.playCmdFailed()
			return
	
		if not self.guideModel.gcamInfo.slitViewer:
			self.statusBar.setMsg("Ctrl-click requires a slit viewer", severity = RO.Constants.sevError)
			self.statusBar.playCmdFailed()
			return
	
		if self.gim.mode != "normal": # recode to use a class constant
			self.statusBar.setMsg("Ctrl-click requires default mode (+ icon)", severity = RO.Constants.sevError)
			self.statusBar.playCmdFailed()
			return
		
		cnvPos = self.gim.cnvPosFromEvt(evt)
		imPos = self.gim.imPosFromCnvPos(cnvPos)
		
		cmdStr = "guide on imgFile=%r centerOn=%.2f,%.2f noGuide %s" % \
			(self.dispImObj.imageName, imPos[0], imPos[1], self.getExpArgStr(inclThresh=False))
		self.doCmd(cmdStr)
	
	def doCenterOnSel(self, evt):
		"""Center up on the selected star.
		"""
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return
		if not self.dispImObj.selDataColor:
			self.statusBar.setMsg("No star selected", severity = RO.Constants.sevWarning)
			return
		
		starData, color = self.dispImObj.selDataColor
		pos = starData[2:4]
		cmdStr = "guide on imgFile=%r centerOn=%.2f,%.2f noGuide %s" % \
			(self.dispImObj.imageName, pos[0], pos[1], self.getExpArgStr(inclThresh=False)
		)
		self.doCmd(cmdStr)
	
	def doChooseIm(self, wdg):
		"""Choose an image to display.
		"""
		self.showCurrWdg.setBool(False)

		if self.dispImObj != None:
			currPath = self.dispImObj.getLocalPath()
			startDir, startFile = os.path.split(currPath)
		else:
			# use user preference for image directory, if available
			startDir = self.tuiModel.prefs.getValue("Save To")
			startFile = None
		newPath = tkFileDialog.askopenfilename(
			initialdir = startDir,
			initialfile = startFile,
			filetypes = (("FITS", "*.fits"), ("FITS", "*.fit"),),
		)
		
		# try to find image in history
		# using samefile is safer than trying to match paths as strings
		# (RO.OS.expandPath *might* be thorough enough to allow that,
		# but no promises and one would have to expand every path being checked)
		for imObj in self.imObjDict.itervalues():
			try:
				isSame = os.path.samefile(newPath, imObj.getLocalPath())
			except OSError:
				continue
			if isSame:
				self.showImage(imObj)
				return
		# not in history; create new local imObj and load that

		# try to split off user's base dir if possible
		baseDir = ""
		imageName = newPath
		startDir = self.tuiModel.prefs.getValue("Save To")
		if startDir != None:
			startDir = RO.OS.expandPath(startDir)
			if startDir and not startDir.endswith(os.sep):
				startDir = startDir + os.sep
			newPath = RO.OS.expandPath(newPath)
			if newPath.startswith(startDir):
				baseDir = startDir
				imageName = newPath[len(startDir):]
		
		imObj = ImObj(
			baseDir = baseDir,
			imageName = imageName,
			cmdChar = "f",
			cmdr = self.tuiModel.getCmdr(),
			cmdID = 0,
			guideModel = self.guideModel,
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
	
	def doCmd(self, cmdStr, actor=None, **kargs):
		"""Execute a command.
		Inputs:
		- cmdStr	the command to execute
		- actor		the actor to which to send the command;
					defaults to the actor for the guide camera
		kargs		any extra kargs are sent to RO.KeyVariable.CmdVar
		"""
		actor = actor or self.actor

		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			self.statusBar.setMsg(cmdStr)
			print cmdStr
	
	def doExistingImage(self, imageName, cmdChar, cmdr, cmdID):
		"""Data is about to arrive for an existing image.
		Decide whether we are interested in it,
		and if so, get ready to receive it.
		"""
		#print "doExistingImage(imageName=%r, cmdChar=%r, cmdr=%r, cmdID=%r" % (imageName, cmdChar, cmdr, cmdID)
		# see if this data is of interest
		imObj = self.imObjDict.get(imageName)
		if not imObj:
			# I have no knowledge of this image, so ignore the data
			return
		isMe = (cmdr == self.tuiModel.getCmdr())
		if not isMe:
			# I didn't trigger this command, so ignore the data
			return
		
		# data is of interest; update cmdr and cmdID
		# and clear sawStarTypes
		imObj.currCmdChar = cmdChar
		imObj.currCmdrCmdID = (cmdr, cmdID)
		imObj.sawStarTypes = []
	
	def doDS9(self, wdg=None):
		"""Display the current image in ds9.
		
		Warning: will need updating once user can display mask;
		lord knows what it'll need once user can display mask*data!
		"""
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return

		# open ds9 window if necessary
		if self.ds9Win:
			# reopen window if necessary
			self.ds9Win.doOpen()
		else:
			self.ds9Win = RO.DS9.DS9Win(self.actor)
		
		localPath = self.dispImObj.getLocalPath()
		self.ds9Win.showFITSFile(localPath)		

	def doExpose(self, wdg=None):
		"""Take an exposure.
		"""
		cmdStr = "findstars " + self.getExpArgStr(inclRadMult=True)
		self.doCmd(cmdStr)
		
	def doFindStars(self, *args):
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return

		radMult = self.radMultWdg.getNum()
		if radMult == None:
			return
		thresh = self.threshWdg.getNum()
		if thresh == None:
			return
		if (radMult == self.dispImObj.currRadMult)\
			and (thresh == self.dispImObj.currThresh):
				return
		
		# not strictly necessary since the hub will return this data;
		# still, it is safer to set it now and be sure it gets set
		self.dispImObj.currThresh = thresh
		self.dispImObj.currRadMult = radMult
		
		# execute new command
		cmdStr = "findstars file=%r thresh=%s radMult=%s" % (self.dispImObj.imageName, thresh, radMult)
		self.doCmd(cmdStr)
		if _LocalMode:
			GuideTest.findStars(self.dispImObj.imageName, thresh=thresh, radMult=radMult)
	
	def doGuideOff(self, wdg=None):
		"""Turn off guiding.
		"""
		sr = self.manGuideScriptRunner
		if sr and sr.isExecuting():
			sr.cancel()
		else:
			cmdStr = "guide off"
			self.doCmd(cmdStr)
	
	def doGuideOn(self, wdg=None):
		"""Guide on the selected star.
		"""
		if not self.dispImObj:
			self.statusBar.setMsg("No guide image", severity = RO.Constants.sevWarning)
			return
		if not self.dispImObj.selDataColor:
			self.statusBar.setMsg("No star selected", severity = RO.Constants.sevWarning)
			return
		
		starData, color = self.dispImObj.selDataColor
		pos = starData[2:4]
		rad = starData[6]
		cmdStr = "guide on imgFile=%r gstar=%.2f,%.2f cradius=%.1f %s" % \
			(self.dispImObj.imageName, pos[0], pos[1], rad, self.getExpArgStr()
		)
		self.doCmd(cmdStr)
		self.enableCmdButtons(isGuiding = True)
	
	def doGuideOnBoresight(self, wdg=None):
		"""Guide on boresight.
		"""
		cmdStr = "guide on boresight %s" % (self.getExpArgStr())
		self.doCmd(cmdStr)
		self.enableCmdButtons(isGuiding = True)
	
	def doManGuide(self, wdg=None):
		"""Repeatedly expose. Let the user control-click to center up.
		"""
		cmdStr = "findstars " + self.getExpArgStr(inclRadMult=True)
		def guideScript(sr, cmdStr=cmdStr):
			# disable Expose, Guide, etc.
			
			# take exposures forever
			while True:
				yield sr.waitCmd(
					actor = self.actor,
					cmdStr = cmdStr,
				)

		self.manGuideScriptRunner = RO.ScriptRunner.ScriptRunner(
			master = self,
			name = "Manual guide script",
			dispatcher = self.tuiModel.dispatcher,
			runFunc = guideScript,
			cmdStatusBar = self.statusBar,
			startNow = True
		)
		self.enableCmdButtons(isGuiding = True)
	
	def doNextIm(self, wdg=None):
		"""Show next image from history list"""
		revHist, currInd = self.getHistInfo()
		if currInd == None:
			self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevWarning)
			return

		if currInd > 0:
			nextImObj = revHist[currInd-1]
		else:
			self.statusBar.setMsg("Showing newest image", severity = RO.Constants.sevWarning)
			return
		
		self.showImage(nextImObj)
	
	def doPrevIm(self, wdg=None):
		"""Show previous image from history list"""
		self.showCurrWdg.setBool(False)

		revHist, currInd = self.getHistInfo()
		if currInd == None:
			self.statusBar.setMsg("Position in history unknown", severity = RO.Constants.sevWarning)
			return

		try:
			prevImObj = revHist[currInd+1]
		except IndexError:
			self.statusBar.setMsg("Showing oldest image", severity = RO.Constants.sevWarning)
			return
		
		self.showImage(prevImObj)
			
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
			if not self.dispImObj:
				return
			
			# erase data for now (helps for early return)
			self.dispImObj.selDataColor = None
	
			# look for nearby centroid to choose
			selStarData = None
			minDistSq = _MaxDist
			for typeChar, starDataList in self.dispImObj.starDataDict.iteritems():
				#print "doSelect checking typeChar=%r, nstars=%r" % (typeChar, len(starDataList))
				tag, color = _TypeTagColorDict[typeChar]
				for starData in starDataList:
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
		if not self.showCurrWdg.getBool():
			return

		# show most recent downloaded image, if any, else most recent image
		revHist = self.imObjDict.values()
		for imObj in revHist:
			if imObj.isDone():
				break
		else:
			# display show most recent image
			imObj = revHist[0]
		
		if imObj == self.dispImObj:
			# image is already being displayed
			imObj = None
				
		if imObj:
			self.showImage(imObj)
		else:
			self.enableHistBtns()
		
	def dragStart(self, evt):
		"""Mouse down for current drag (whatever that might be).
		"""
		if not self.gim.isNormalMode():
			return
		self.dragStart = self.gim.cnvPosFromEvt(evt)
		self.dragRect = self.gim.cnv.create_rectangle(
			self.dragStart[0], self.dragStart[1], self.dragStart[0], self.dragStart[1],
			outline = _CentroidColor,
			tags = _DragRectTag,
		)
	
	def dragContinue(self, evt):
		if self.inCtrlClick:
			return
		if not self.gim.isNormalMode():
			return
		newPos = self.gim.cnvPosFromEvt(evt)
		self.gim.cnv.coords(self.dragRect, self.dragStart[0], self.dragStart[1], newPos[0], newPos[1])
	
	def dragEnd(self, evt):
		if self.inCtrlClick:
			self.inCtrlClick = False
			return

		if not self.gim.isNormalMode():
			return

		endPos = self.gim.cnvPosFromEvt(evt)
		startPos = self.dragStart or endPos

		self.gim.cnv.delete(_DragRectTag)
		self.dragStart = None
		self.dragRect = None
		
		if not self.dispImObj:
			return

		meanPos = num.divide(num.add(startPos, endPos), 2.0)
		deltaPos = num.subtract(endPos, startPos)

		rad = max(deltaPos) / (self.gim.zoomFac * 2.0)
		imPos = self.gim.imPosFromCnvPos(meanPos)
		thresh = self.threshWdg.getNum()
		
		if abs(deltaPos[0]) > 1 and abs(deltaPos[1] > 1):
			# centroid

			# execute centroid command
			cmdStr = "centroid file=%r on=%s,%s radius=%s thresh=%s" % (self.dispImObj.imageName, imPos[0], imPos[1], rad, thresh)
			self.doCmd(cmdStr)
			if _LocalMode:
				GuideTest.centroid(self.dispImObj.imageName, on=imPos, rad=rad, thresh=thresh)
			
		else:
			# select
			self.doSelect(evt)
	
	def enableCmdBtns(self, isGuiding=None):
		"""Set enable of command buttons.
		
		If you specify isGuiding then the value you specify will be used
		(used to disable guide on buttons just after pressing one).
		"""
		isImage = (self.dispImObj != None)
		isSel = (self.dispImObj != None) and (self.dispImObj.selDataColor != None)
		if isGuiding == None:
			isGuiding = self.isGuiding()
		
		# set enable for buttons that can change; all others are always enabled
		self.centerBtn.setEnable(isImage and isSel and not isGuiding)
		self.guideOnBtn.setEnable(isImage and isSel and not isGuiding)
		self.guideOnBoresightBtn.setEnable(not isGuiding)
		self.guideOffBtn.setEnable(isGuiding)
		self.ds9Btn.setEnable(isImage)		
	
	def enableHistBtns(self):
		"""Set enable of prev and next buttons"""
		revHist, currInd = self.getHistInfo()
#		print "currInd=%s, len(revHist)=%s, revHist=%s" % (currInd, len(revHist), revHist)
		enablePrev = False
		enableNext = False
		if (len(revHist) > 0) and (currInd != None):
			if currInd < len(revHist) - 1:
				enablePrev = True
				
			if not self.showCurrWdg.getBool() and (currInd > 0):
				enableNext = True
		
			self.prevImWdg.setEnable(enablePrev)
			self.nextImWdg.setEnable(enableNext)
		
	def fetchCallback(self, imObj):
		"""Called when an image is finished downloading.
		"""
		if self.showCurrWdg.getBool():
			self.showImage(imObj)
	
	def getExpArgStr(self, inclThresh = True, inclRadMult = False):
		"""Return exposure time, bin factor, thresh and radMult
		as a string suitable for a guide camera command.
		
		The defaults are suitable for autoguiding.
		Set inclRadMult true for finding stars.
		Set inclRadMult false for manual guiding.
		"""
		argList = []
		expTimeStr = self.expTimeWdg.getString()
		if expTimeStr:
			argList.append("exptime=" + expTimeStr)

		binFacStr = self.binFacWdg.getString()
		if binFacStr:
			argList.append("bin=" + binFacStr)

		if inclRadMult:
			radMultStr = self.radMultWdg.getString()
			if radMultStr:
				argList.append("radMult=" + radMultStr)
		
		if inclThresh:
			threshStr = self.threshWdg.getString()
			if threshStr:
				argList.append("thresh=" + threshStr)
		
		return " ".join(argList)
	
	def getHistInfo(self):
		"""Return information about the location of the current image in history.
		Returns:
		- revHist: list of image objects in history in reverse order (most recent first)
		- currImInd: index of displayed image in history
		  or None if no image is displayed or displayed image not in history at all
		"""
		revHist = self.imObjDict.values()
		try:
			currImInd = revHist.index(self.dispImObj)
		except (ValueError, IndexError):
			currImInd = None
		return (revHist, currImInd)
	
	def getGuidingInfo(self):
		"""Return guide state, isGuiding (True if guiding is starting or on).
		This is a bit of a hack to help handle StarQuality
		and NoGuideStar keywords. Thus it returns false for isGuiding
		if the guiding keyword is not current.
		"""
		guideState, guideStateCurr = self.guideModel.guiding.getInd(0)
		if not guideStateCurr:
			isGuiding = False
		else:
			isGuiding = guideState.lower() in ("on", "starting")
		return guideState, isGuiding
	
	def ignoreEvt(self, evt=None):
		pass
	
	def isGuiding(self):
		"""Return True if guiding"""
		guideState, guideStateCurr = self.guideModel.guiding.getInd(0)
		if guideState == None:
			return False
		return guideState.lower() in ("on", "starting")
	
	def showImage(self, imObj):
		"""Display an image.
		"""
		self._showShim(imObj)
	
	def _showShim(self, imObj):
		# delete image from disk, if no longer in history
		if (self.dispImObj != None) and (self.dispImObj.imageName not in self.imObjDict):
			# purge file
			self.dispImObj.expire()
		
		#print "showImage(imObj=%s)" % (imObj,)
		if imObj == None:
			self.statusBar.setMsg("", RO.Constants.sevNormal)
			imArr = None
			expTime = None
			binFac = None
			self.imNameWdg.set(None)
			self.expTimeWdg.set(None)
			self.expTimeWdg.setDefault(None)
			self.binFacWdg.set(None)
			self.binFacWdg.setDefault(None)
			self.threshWdg.setDefault(None)
			self.radMultWdg.setDefault(None)
			return
			
		fitsIm = imObj.getFITSObj()
		if not fitsIm:
			if imObj.didFail():
				sev = RO.Constants.sevError
			else:
				sev = RO.Constants.sevWarning
			self.statusBar.setMsg("Image %r: %s" % (imObj.imageName, imObj.getStateStr()), sev)
			imArr = None
			expTime = None
			binFac = None
		else:
			self.statusBar.setMsg("", RO.Constants.sevNormal)
			imArr = fitsIm[0].data
			imHdr = fitsIm[0].header
			expTime = imHdr.get("EXPTIME")
			binFac = imHdr.get("BINX")
	
		# display new data
		self.gim.showArr(imArr)
		self.dispImObj = imObj
		self.imNameWdg["text"] = imObj.imageName
		self.expTimeWdg.set(expTime)
		self.expTimeWdg.setDefault(expTime)
		self.binFacWdg.set(binFac)
		self.binFacWdg.setDefault(binFac)
		self.threshWdg.setDefault(imObj.defThresh)
		self.radMultWdg.setDefault(imObj.defRadMult)
		if imObj.currThresh != None:
			self.threshWdg.set(imObj.currThresh)
		else:
			self.threshWdg.restoreDefault()
		if imObj.currRadMult != None:
			self.radMultWdg.set(imObj.currRadMult)
		else:
			self.radMultWdg.restoreDefault()
		
		self.enableHistBtns()
		
		if imArr != None:
			# add existing annotations, if any and show selection
			# (for now just display them,
			# but eventually have a control that can show/hide them,
			# and -- as the first step -- set the visibility of the tags appropriately)
			for cmdChar, starDataList in imObj.starDataDict.iteritems():
				for starData in starDataList:
					tag, color = _TypeTagColorDict[cmdChar]
					self.gim.addAnnotation(
						GImDisp.ann_Circle,
						imPos = starData[2:4],
						rad = starData[6],
						isImSize = True,
						tags = tag,
						outline = color,
					)
			
			self.showSelection()

	def showSelection(self):
		"""Display the current selection.
		"""
		# clear current selection
		self.gim.removeAnnotation(_SelTag)

		if not self.dispImObj or not self.dispImObj.selDataColor:
			# disable command buttons accordingly
			self.enableCmdBtns()
			
			# clear data display
			self.starXPosWdg.set(None)
			self.starYPosWdg.set(None)
			self.starFWHMWdg.set(None)
			self.starAmplWdg.set(None)
			self.starBkgndWdg.set(None)
			return
		
		starData, color = self.dispImObj.selDataColor

		# draw selection
		selID = self.gim.addAnnotation(
			GImDisp.ann_X,
			imPos = starData[2:4],
			isImSize = False,
			rad = _MarkRad,
			holeRad = _HoleRad,
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
		self.enableCmdBtns()
		
	def updFiles(self, fileData, isCurrent, keyVar):
		"""Handle files keyword
		"""
		#print "%s updFiles(fileData=%r; isCurrent=%r)" % (self.actor, fileData, isCurrent)
		if not isCurrent:
			return
		
		cmdChar, isNew, baseDir, imageName, maskName = fileData[0:5]
		msgDict = keyVar.getMsgDict()
		cmdr = msgDict["cmdr"]
		cmdID = msgDict["cmdID"]
		imageName = baseDir + imageName
		if maskName:
			maskName = baseDir + maskName

		if not isNew:
			# handle data for existing image
			self.doExistingImage(imageName, cmdChar, cmdr, cmdID)
			return
		
		# at this point we know we have a new image
		
		if not self.winfo_ismapped():
			# window is not visible; do NOT download files
			# wait until we know it's a new image to test for this
			# because if we have downloaded a file
			# then we should record the data that goes with it
			#print "not downloading %r because %s window is hidden" % (imageName, self.actor)
			self.showImage(None)
			return				
		
		# create new object data
		baseDir = self.guideModel.ftpSaveToPref.getValue()
		msgDict = keyVar.getMsgDict()
		cmdr = msgDict["cmdr"]
		cmdID = msgDict["cmdID"]
		defRadMult = self.guideModel.fsDefRadMult.getInd(0)[0]
		defThresh = self.guideModel.fsDefThresh.getInd(0)[0]
		imObj = ImObj(
			baseDir = baseDir,
			imageName = imageName,
			cmdChar = cmdChar,
			cmdr = cmdr,
			cmdID = cmdID,
			guideModel = self.guideModel,
			fetchCallFunc = self.fetchCallback,
			defRadMult = defRadMult,
			defThresh = defThresh,
		)
		self._trackMem(imObj, str(imObj))
		self.addImToHist(imObj)
		imObj.fetchFile()
		if (self.dispImObj == None or self.dispImObj.didFail()) and self.showCurrWdg.getBool():
			self.showImage(imObj)

		# associate mask data, creating it if necessary
		if maskName:
			maskObj = self.maskDict.get(maskName)
			if not maskObj:
				maskObj = BasicImObj(
					baseDir = baseDir,
					imageName = maskName,
					guideModel = self.guideModel,
				)
				self.maskDict[maskName] = maskObj
# once you know what to do with mask files, start fetching them
# but some callback should be listening for them
# and there should be some easy way to display them
#				maskObj.fetchFile()
			imObj.maskObj = maskObj

		# purge excess images
		if self.dispImObj:
			dispImName = self.dispImObj.imageName
		else:
			dispImName = ()
		if len(self.imObjDict) > self.nToSave:
			keys = self.imObjDict.keys()
			for imName in keys[self.nToSave:]:
				if imName == dispImName:
					continue
				if _DebugMem:
					print "Purging %r from history" % (imName,)
				purgeImObj = self.imObjDict.pop(imName)
				purgeImObj.expire()
	
	def updGuiding(self, guideState, isCurrent, **kargs):
		if not isCurrent:
			return
		self.guideStateWdg.set(
			guideState[0],
			severity = RO.Constants.sevNormal,
		)
		self.enableCmdBtns()
	
	def updNoGuideStar(self, nullData, isCurrent, **kargs):
		if not isCurrent:
			return
		guideState, isGuiding = self.getGuidingInfo()
		if not isGuiding:
			return
		self.guideStateWdg.set(
			"%s; No Guide Star" % (guideState,),
			severity = RO.Constants.sevWarning,
		)
	
	def updStarQuality(self, starQuality, isCurrent, **kargs):
		if not isCurrent or starQuality == None:
			return
		guideState, isGuiding = self.getGuidingInfo()
		if not isGuiding:
			return
		self.guideStateWdg.set(
			"%s; Star Quality = %2.1f" % (guideState, starQuality,),
			severity = RO.Constants.sevNormal,
		)

	def updStar(self, starData, isCurrent, keyVar):
		"""New star data found.
		
		Overwrite existing findStars data if:
		- No existing data and cmdr, cmdID match
		- I generated the command
		else ignore.
		
		Replace existing centroid data if I generated the command,
		else ignore.
		"""
		#print "%s updStar(starData=%r, isCurrent=%r)" % (self.actor, starData, isCurrent)
		if not isCurrent:
			return

		# get image object (ignore if no match)
		msgDict = keyVar.getMsgDict()
		cmdrCmdID = (msgDict["cmdr"], msgDict["cmdID"])
		for imObj in self.imObjDict.itervalues():
			if cmdrCmdID == imObj.currCmdrCmdID:
				break
		else:
			return
		
		isVisible = (self.dispImObj and self.dispImObj.imageName == imObj.imageName)
		typeChar = starData[0]
		try:
			tag, color = _TypeTagColorDict[typeChar]
		except KeyError:
			raise RuntimeError("Unknown type character %r for star data" % (typeChar,))

		updSel = False
		if typeChar in imObj.sawStarTypes:
			# add star data
			imObj.starDataDict[typeChar].append(starData)
		else:	
			# first star data of this type seen for this command;
			# update selection if necessary and restart this type of data
			if not imObj.sawStarTypes:
				# first star data of ANY type seen for this command; reset selection
				imObj.selDataColor = (starData, color)
				updSel = True

			# reset this type of data
			imObj.starDataDict[typeChar] = [starData]
			imObj.sawStarTypes.append(typeChar)

			if isVisible:
				self.gim.removeAnnotation(tag)

		if not isVisible:
			# this image is not being displayed, so we're done
			return
		
		# update the display
		self.gim.addAnnotation(
			GImDisp.ann_Circle,
			imPos = starData[2:4],
			rad = starData[6],
			isImSize = True,
			tags = tag,
			outline = color,
		)
		
		# if this star was selected, display selection
		if updSel:
			self.showSelection()
	
	def updRadMult(self, radMult, isCurrent, keyVar):
		"""New radMult data found.
		"""
		#print "%s updRadMult(radMult=%r, isCurrent=%r)" % (self.actor, radMult, isCurrent)
		if not isCurrent:
			return

		# get image object (ignore if no match)
		msgDict = keyVar.getMsgDict()
		cmdrCmdID = (msgDict["cmdr"], msgDict["cmdID"])
		for imObj in self.imObjDict.itervalues():
			if cmdrCmdID == imObj.currCmdrCmdID:
				break
		else:
			return
		
		if imObj.currRadMult == None:
			imObj.defRadMult = radMult
		imObj.currRadMult = radMult

		isVisible = (self.dispImObj and self.dispImObj.imageName == imObj.imageName)
		if isVisible:
			self.radMultWdg.setDefault(imObj.defRadMult)
			self.radMultWdg.set(imObj.currRadMult)

	def updThresh(self, thresh, isCurrent, keyVar):
		"""New threshold data found.
		"""
		#print "%s updThresh(thresh=%r, isCurrent=%r)" % (self.actor, thresh, isCurrent)
		if not isCurrent:
			return

		# get image object (ignore if no match)
		msgDict = keyVar.getMsgDict()
		cmdrCmdID = (msgDict["cmdr"], msgDict["cmdID"])
		for imObj in self.imObjDict.itervalues():
			if cmdrCmdID == imObj.currCmdrCmdID:
				break
		else:
			return
		
		if imObj.currThresh == None:
			imObj.defThresh = thresh
		imObj.currThresh = thresh

		isVisible = (self.dispImObj and self.dispImObj.imageName == imObj.imageName)
		if isVisible:
			self.threshWdg.setDefault(imObj.defThresh)
			self.threshWdg.set(imObj.currThresh)
	
	def _exitHandler(self):
		"""Delete all image files and mask files.
		"""
		for maskObj in self.maskDict.itervalues():
			maskObj.expire()
		for imObj in self.imObjDict.itervalues():
			imObj.expire()
		

if __name__ == "__main__":
	#import gc
	#gc.set_debug(gc.DEBUG_SAVEALL) # or gc.DEBUG_LEAK to print lots of messages
	
	doLocal = False  # run local tests?
	
	if doLocal:
		_LocalMode = True
	
	_HistLen = 5

	root = RO.Wdg.PythonTk()

	GuideTest.init("ecam", doFTP = True)	

	testFrame = GuideWdg(root, "ecam")
	testFrame.pack(expand="yes", fill="both")

	if doLocal:
		GuideTest.runLocalDemo()
	else:
		GuideTest.runDownload(
			basePath = "keep/gcam/UT050422/",
			startNum = 101,
			numImages = 100,
			maskNum = 1,
			waitMs = 2500,
		)

	root.mainloop()
