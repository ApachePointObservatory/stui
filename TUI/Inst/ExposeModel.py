#!/usr/bin/env python
"""Model for exposures (data from the expose command).
A different model is required for each instrument,
but there are only a few minor differences.

Notes:
- At this time, nextPath is the only keyword reliably returned by keys for <inst>Expose.
  Thus it is the only keyword with a refresh command.
  Fix this when the expose command is fixed.

2003-07-16 ROwen
2003-07-25 ROwen    Added expState, seqState, nFiles
2003-07-30 ROwen    Added inst-specific info and getModel
2003-10-01 ROwen    Modified to use new versions of seqState and expState (for new hub).
2003-10-06 ROwen    Modified to use new versions of files and nextPath (for new hub).
2003-10-10 ROwen    Modified actor to match change in hub expose.
2003-10-16 ROwen    Bug fix: some refresh commands had not been updated for the new hub.
2003-10-22 ROwen    Bug fix: GRIM min exposure time is >1.21, not >=1.21 sec,
                    so I set the lower limit to 1.22.
2003-12-17 ROwen    Modified to use KeyVariable.KeyVarFactory
                    and to take advantage of key variables now
                    auto-setting nval if a set of converters is supplied.
2004-01-06 ROwen    Modified to use KeyVarFactory.setKeysRefreshCmd.
2004-08-27 ROwen    Added new <inst>NewFiles keyword.
2004-09-10 ROwen    Moved auto ftp code here from ExposeInputWdg.
                    Added several ftp-related entries.
                    Added formatExpCmd (to make scripting easier).
                    Replaced model.dispatcher with model.tuiModel.
                    Added __all__ to improve "from ExposeModel import *".
2004-09-28 ROwen    Added comment entry.
2004-10-19 ROwen    Added nicfps to _InstInfoDict.
2004-11-16 ROwen    Modified to explicitly ask for binary ftp
                    (instead of relying on the ftp server to be smart).
2004-11-17 ROwen    Modified for changed RO.Comm.FTPLogWdg.
2004-11-29 ROwen    Changed nicfps minimum expose time to 0.
2004-12-20 ROwen    Listed the allowed states for expState and seqState.
2005-06-14 ROwen    Removed instrument info for grim.
                    Changed the test code to auto-select instrument names.
2005-07-08 ROwen    Modified for http download.
2005-07-13 ROwen    Bug fix: formatExpCmd rejected 0 as a missing exposure time.
2005-07-21 ROwen    Modified to fully quote the file name (meaningless now because special
                    characters aren't allowed, but in case that restriction is lifted...).
2005-09-15 ROwen    Replaced autoFTPPref -> autoFTPVar to allow user to toggle it
                    for this instrument w/out affecting other instruments.
                    Users logged into program APO are everyone's collaborators.
                    Added viewImageVar and added image view support. Warning:
                    it blocks events while the ds9 window is opened,
                    which can be a long time if there's an error.
2005-09-23 ROwen    Fix PR 269: Seq By File preference cannot be unset.
                    Fixed by alwys specifying seq (the <inst>Expose documentation
                    says the default is seqByDir, but it seems to be the last seq used).
                    View Image improvements:
                    - Use a separate ds9 window for each camera.
                    - Re-open a ds9 window if necessary.
2005-09-26 ROwen    Added canPause, canStop, canAbort attributes to ExpInfo.
                    If RO.DS9 fails, complain to the log window.
2007-05-22 ROwen    Added SPIcam.
2007-07-27 ROwen    Set min exposure time for SPIcam to 0.76 seconds.
2008-03-14 ROwen    Added information for TripleSpec.
                    Added instName and actor arguments to _ExpInfo class.
2008-03-25 ROwen    Split actor into instActor and exposeActor in _ExpInfo class.
                    Changed instrument name TripleSpec to TSpec.
2008-04-23 ROwen    Get expState from the cache (finally) but null out the times.
                    Modified expState so durations can be None or 0 for unknown (was just 0).
2008-04-29 ROwen    Fixed reporting of exceptions that contain unicode arguments.
2008-10-24 ROwen    Added information for Agile.
2008-11-06 ROwen    Added imSize, bin, window and overscan data to instInfo.
                    Added bin, window and overscan arguments to formatExpCmd.
"""
__all__ = ['getModel']

import os
import Tkinter
import RO.Alg
import RO.Astro.ImageWindow
import RO.CnvUtil
import RO.DS9
import RO.KeyVariable
import RO.SeqUtil
import RO.StringUtil
import TUI.HubModel
import TUI.TUIModel

class _ExpInfo:
    """Exposure information for a camera
    
    Inputs:
    - instName: the instrument name (in the preferred case)
    - imSize: the size of the image (e.g. CCD) in unbinned pixels; a pair of ints
    - instActor: the instrument's actor (defaults to instName.lower())
    - min/maxExpTime: minimum and maximum exposure time (sec)
    - camNames: name of each camera (if more than one)
    - expTypes: types of exposures supported
    - canPause: instrument can pause an exposure
    - canStop: instrument can stop an exposure
    - canAbort: instrument can abort an exposure
    - numBin: number of axes of bin the user can supply as part of expose command (0, 1 or 2)
    - defBin: default bin factor; a sequence of numBin elements;
            if numBin = 1 then you may specify an integer, which is converted to a list of 1 int
            if None then defaults to a list the right number of 1s.
    - canWindow: can specify window as part of expose command
    - canOverscan: can specify overscan as part of expose command
    - isOneBased: corner pixel is 1,1 (true) or 0,0 (false)
    - isInclusive: window end is included (true) or not included (false) in image
    """
    def __init__(self,
        instName,
        imSize,
        instActor = None,
        minExpTime = 0.1,
        maxExpTime = 12 * 3600,
        camNames = None,
        expTypes = ("object", "flat", "dark", "bias"),
        canPause = True,
        canStop = True,
        canAbort = True,
        numBin = 0,
        defBin = None,
        canWindow = False,
        canOverscan = False,
        isOneBased = True,
        isInclusive = True,
    ):
        self.instName = str(instName)
        if len(imSize) != 2:
            raise RuntimeError("imSize=%s must contain two ints" % (imSize,))
        self.imSize = [int(val) for val in imSize]
        if instActor != None:
            self.instActor = str(instActor)
        else:
            self.instActor = instName.lower()
        self.exposeActor = "%sExpose" % (self.instActor,)
        self.minExpTime = minExpTime
        self.maxExpTime = maxExpTime
        if camNames == None:
            camNames = ("",)
        self.camNames = camNames
        self.expTypes = expTypes
        self.canPause = bool(canPause)
        self.canStop = bool(canStop)
        self.canAbort = bool(canAbort)
        self.numBin = int(numBin)
        if not (0 <= self.numBin <= 2):
            raise RuntimeError("numBin=%s not in range [0,2]" % (self.numBin,))
        if defBin == None:
            defBinList = [1]*self.numBin
        else:
            defBinList = [int(val) for val in RO.SeqUtil.asList(defBin)]
            if len(defBinList) != self.numBin:
                raise RuntimeError("defBin=%s should have %d elements" % (defBin, self.numBin,))
        self.defBin = defBinList
        self.canWindow = bool(canWindow)
        self.canOverscan = bool(canOverscan)
        self.isOneBased = bool(isOneBased)
        self.isInclusive = bool(isInclusive)
    
    def getNumCameras(self):
        return len(self.camNames)

def _getInstInfoDict():
    # instrument information
    _InstInfoList = (
        _ExpInfo(
            instName = "agile",
            imSize = (1024, 1024),
            minExpTime = 1,
            canPause = False,
            canStop = False,
            numBin = 1,
            canWindow = True,
            canOverscan = True,
            isOneBased = False,
        ),
        _ExpInfo(
            instName = "DIS",
            imSize = (2048, 1028),
            minExpTime = 1, 
            camNames = ("blue", "red"),
        ),
        _ExpInfo(
            instName = "Echelle",
            imSize = (2048, 2048),
        ),
        _ExpInfo(
            instName = "NICFPS",
            imSize = (1024, 1024),
            minExpTime = 0, 
            expTypes = ("object", "flat", "dark"),
            canPause = False,
            canAbort = False,
        ),
        _ExpInfo(
            instName = "SPIcam",
            minExpTime = 0.76,
            imSize = (2048, 2048),
        ),
        _ExpInfo(
            instName = "TSpec",
            imSize = (2048, 1024),
            minExpTime = 0.75,
            expTypes = ("object", "flat", "dark"),
            canPause = False,
            canStop = False,
        ),
    )
    
    instInfoDict = {}
    for instInfo in _InstInfoList:
        instInfoDict[instInfo.instName.lower()] = instInfo
    return instInfoDict

# dictionary of instrument information
_InstInfoDict = _getInstInfoDict()

# cache of instrument exposure models
# each entry is instName: model
_modelDict = {}

class _BoolPrefToVar:
    """Class to set a Tkinter variable
    from a RO.Pref preference variable.
    If the preference value changes,
    the variable changes, but not visa versa
    """
    def __init__(self, pref):
        self.var = Tkinter.BooleanVar()
        pref.addCallback(self, callNow=True)
    def __call__(self, prefVal, pref=None):
        self.var.set(bool(prefVal))

def getModel(instName):
    global _modelDict
    instNameLow = instName.lower()
    model = _modelDict.get(instNameLow)
    if model == None:
        model = Model(instName)
        _modelDict[instNameLow] = model
    return model


class Model (object):
    def __init__(self, instName):
        self.instName = instName
        self.instNameLow = instName.lower()
        self.instInfo = _InstInfoDict[self.instNameLow]
        self.actor = self.instInfo.exposeActor
        self.ds9WinDict = {}
        
        self.hubModel = TUI.HubModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()
        
        
        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            dispatcher = self.tuiModel.dispatcher,
            converters = str,
            allowRefresh = False,
        )

        self.exposeTxt = keyVarFact(
            keyword="exposeTxt",
            description="progress report for current sequence",
            allowRefresh = False,
        )

        self.expState = keyVarFact(
            keyword = self.instName + "ExpState",
            converters = (str, str, str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asFloatOrNone),
            description = """current exposure info:
            - cmdr (progID.username)
            - exposure state; one of: idle, flushing, integrating, paused,
                reading, processing, aborting, done or aborted.
            - start time (an ANSI-format UTC timestamp)
            - remaining time for this state (sec; 0 or None if short or unknown)
            - total time for this state (sec; 0 or None if short or unknown)
            
            Note: if the data is cached then remaining time and total time
            are changed to 0 to indicate that the values are unknown
            """,
            allowRefresh = False, # do not use an archived value
        )
        self.expState.addCallback(self._updExpState)

        self.files = keyVarFact(
            keyword = self.instName + "Files",
            nval = 5 + self.instInfo.getNumCameras(),
            description = """file(s) just saved:
            - cmdr (progID.username)
            - host
            - common root directory
            - program and date subdirectory
            - user subdirectory
            - file name(s)
            
            This keyword is only output when a file is saved.
            It is not output as a result of status.
            
            The full path to a file is the concatenation of common root, program subdir, user subdir and file name.
            If a file in a multi-file instrument is not saved,
            the missing file name is omitted (but the comma remains).
            """,
            allowRefresh = False,
        )

        self.newFiles = keyVarFact(
            keyword = self.instName + "NewFiles",
            nval = 5 + self.instInfo.getNumCameras(),
            description = """file(s) that will be saved at the end of the current exposure:
            - cmdr (progID.username)
            - host
            - common root directory
            - program and date subdirectory
            - user subdirectory
            - file name(s)
            
            The full path to a file is the concatenation of common root, program subdir, user subdir and file name.
            If a file in a multi-file instrument is not saved,
            the missing file name is omitted (but the comma remains).
            """,
            allowRefresh = False, # change to True if/when <inst>Expose always outputs it with status
        )

        self.nextPath = keyVarFact(
            keyword = self.instName + "NextPath",
            nval = 5,
            description = """default file settings (used for the next exposure):
            - cmdr (progID.username)
            - user subdirectory
            - file name prefix
            - sequence number (with leading zeros)
            - file name suffix
            """,
            allowRefresh = True,
        )
        
        self.seqState = keyVarFact(
            keyword = self.instName + "SeqState",
            converters = (str, str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asInt, RO.CnvUtil.asInt, str),
            description = """current sequence info:
            - cmdr (progID.username)
            - exposure type
            - exposure duration
            - exposure number
            - number of exposures requested
            - sequence state; one of: running, paused, aborted, stopped, done or failed
            """,
            allowRefresh = True,
        )
        
        self.comment = keyVarFact(
            keyword = "comment",
            converters = str,
            description = "comment string",
            allowRefresh = False, # change to True if/when <inst>Expose always outputs it with status
        )
        
        if self.instInfo.numBin > 0:
            self.bin = keyVarFact(
                keyword = "bin",
                nval = self.instInfo.numBin,
                converters = int,
                description = {1: "bin factor (x=y)", 2: "x, y bin factor"}[self.instInfo.numBin],
                allowRefresh = True,
            )

        if self.instInfo.canWindow:
            self.window = keyVarFact(
                keyword = "window",
                nval = 4,
                converters = int,
                description = "window: LL x, y; UR x, y (inclusive, binned pixels)",
                allowRefresh = True,
            )
        
        if self.instInfo.canOverscan:
            self.overscan = keyVarFact(
                keyword = "overscan",
                nval = 2,
                converters = int,
                description = "x, y overscan (binned pixels)",
                allowRefresh = True,
            )
        
        # utility to convert between binned and unbinned windows
        self.imageWindow = RO.Astro.ImageWindow.ImageWindow(
            imSize = self.instInfo.imSize,
            isOneBased = self.instInfo.isOneBased,
            isInclusive = self.instInfo.isInclusive,
        )
        
        keyVarFact.setKeysRefreshCmd(getAllKeys=True)
        
        # entries for file numbering and auto ftp, including:
        # variables for items the user may toggle
        # pointers to prefs for items the user can only set via prefs
        # a pointer to the download widget
        autoGetPref = self.tuiModel.prefs.getPrefVar("Auto Get")
        self.autoGetVar = _BoolPrefToVar(autoGetPref).var
        viewImagePref = self.tuiModel.prefs.getPrefVar("View Image")
        self.viewImageVar = _BoolPrefToVar(viewImagePref).var

        self.getCollabPref = self.tuiModel.prefs.getPrefVar("Get Collab")
        self.ftpSaveToPref = self.tuiModel.prefs.getPrefVar("Save To")
        self.seqByFilePref = self.tuiModel.prefs.getPrefVar("Seq By File")
        
        downloadTL = self.tuiModel.tlSet.getToplevel("TUI.Downloads")
        self.downloadWdg = downloadTL and downloadTL.getWdg()
        
        if self.downloadWdg:
            # set up automatic ftp; we have all the info we need
            self.files.addCallback(self._updFiles)

    def formatExpCmd(self,
        expType = "object",
        expTime = None,
        cameras = None,
        fileName = "",
        numExp = 1,
        startNum = None,
        totNum = None,
        comment = None,
        bin = None,
        window = None,
        overscan = None,
    ):
        """Format an exposure command.
        Raise ValueError or TypeError for invalid inputs.
        """
        outStrList = []
        
        expType = expType.lower()
        if expType not in self.instInfo.expTypes:
            raise ValueError("unknown exposure type %r" % (expType,))
        outStrList.append(expType)
        
        if expType.lower() != "bias":
            if expTime == None:
                raise ValueError("exposure time required")
            outStrList.append("time=%.2f" % (expTime))
        
        if cameras != None:
            camList = RO.SeqUtil.asSequence(cameras)
            for cam in camList:
                cam = cam.lower()
                if cam not in self.instInfo.camNames:
                    raise ValueError("unknown camera %r" % (cam,))
                outStrList.append(cam)
    
        outStrList.append("n=%d" % (numExp,))

        if not fileName:
            raise ValueError("file name required")
        outStrList.append("name=%s" % (RO.StringUtil.quoteStr(fileName),))
            
        if self.seqByFilePref.getValue():
            outStrList.append("seq=nextByFile")
        else:
            outStrList.append("seq=nextByDir")
        
        if startNum != None:
            outStrList.append("startNum=%d" % (startNum,))
        
        if totNum != None:
            outStrList.append("totNum=%d" % (totNum,))
        
        if bin:
            if self.instInfo.numBin < 1:
                raise ValueError("Cannot specify bin in %s expose command" % (self.instInfo.instName,))
            outStrList.append(formatValList("bin", bin, "%d", self.instInfo.numBin))
        
        if window:
            if not self.instInfo.canWindow:
                raise ValueError("Cannot specify window in %s expose command" % (self.instInfo.instName,))
            outStrList.append(formatValList("window", window, "%d", 4))
        
        if overscan:
            if not self.instInfo.canOverscan:
                raise ValueError("Cannot specify overscan in %s expose command" % (self.instInfo.instName,))
            outStrList.append(formatValList("overscan", overscan, "%d", 2))
        
        if comment != None:
            outStrList.append("comment=%s" % (RO.StringUtil.quoteStr(comment),))
    
        return " ".join(outStrList)
    
    def _downloadFinished(self, camName, httpGet):
        """Call when an image file has been downloaded"""
        if httpGet.getState() != httpGet.Done:
            return
        ds9Win = self.ds9WinDict.get(camName)
        try:
            if not ds9Win:
                if camName not in self.instInfo.camNames:
                    raise RuntimeError("Unknown camera name %r for %s" % (camName, self.instName))
                if camName:
                    ds9Name = "%s_%s" % (self.instName, camName)
                else:
                    ds9Name = self.instName
                ds9Win = RO.DS9.DS9Win(ds9Name, doOpen=True)
                self.ds9WinDict[camName] = ds9Win
            elif not ds9Win.isOpen():
                ds9Win.doOpen()
            ds9Win.showFITSFile(httpGet.toPath)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            self.tuiModel.logMsg(
                msgStr = RO.StringUtil.strFromException(e),
                severity = RO.Constants.sevError,
            )
    
    def _updExpState(self, expState, isCurrent, keyVar):
        """Set the durations to None (unknown) if data is from the cache"""
        if keyVar.isGenuine():
            return
        modValues = list(expState)
        modValues[3] = None
        modValues[4] = None
        keyVar._valueList = tuple(modValues)
        
    def _updFiles(self, fileInfo, isCurrent, keyVar):
        """Call whenever a file is written
        to start an ftp download (if appropriate).
        
        fileInfo consists of:
        - cmdr (progID.username)
        - host
        - common root directory
        - program and date subdirectory
        - user subdirectory
        - file name(s) for most recent exposure
        """
        if not isCurrent:
            return
#       print "_updFiles(%r, %r)" % (fileInfo, isCurrent)
        if not self.autoGetVar.get():
            return
        if not keyVar.isGenuine():
            # cached; avoid redownloading
            return
        
        cmdr, dumHost, dumFromRootDir, progDir, userDir = fileInfo[0:5]
        progID, username = cmdr.split(".")
        fileNames = fileInfo[5:]
        
        host, fromRootDir = self.hubModel.httpRoot.get()[0]
        if None in (host, fromRootDir):
            errMsg = "Cannot download images; hub httpRoot keyword not available"
            self.tuiModel.logMsg(errMsg, RO.Constants.sevWarning)
            return
        
        if self.tuiModel.getProgID() not in (progID, "APO"):
            # files are for a different program; ignore them unless user is APO
            return
        if not self.getCollabPref.getValue() and username != self.tuiModel.getUsername():
            # files are for a collaborator and we don't want those
            return
        
        toRootDir = self.ftpSaveToPref.getValue()

        # save in userDir subdirectory of ftp directory
        for ii in range(len(fileNames)):
            fileName = fileNames[ii]
            if fileName == "None":
                continue

            dispStr = "".join((progDir, userDir, fileName))
            fromURL = "".join(("http://", host, fromRootDir, progDir, userDir, fileName))
            toPath = os.path.join(toRootDir, progDir, userDir, fileName)
            
            doneFunc = None
            if self.viewImageVar.get():
                camName = RO.SeqUtil.get(self.instInfo.camNames, ii)
                if camName != None:
                    doneFunc = RO.Alg.GenericCallback(self._downloadFinished, camName)
                else:
                    self.tuiModel.logMsg(
                        "More files than known cameras; cannot display image %s" % fileName,
                        severity = RO.Constants.sevWarning,
                    )
            
            self.downloadWdg.getFile(
                fromURL = fromURL,
                toPath = toPath,
                isBinary = True,
                overwrite = False,
                createDir = True,
                dispStr = dispStr,
                doneFunc = doneFunc,
            )

def formatValList(name, valList, valFmt, numElts=None):
    print "formatValList(name=%r, valList=%s, valFmt=%r, numElts=%s)" % (name, valList, valFmt, numElts)
    if numElts != None and len(valList) != numElts:
        raise ValueError("%s=%s; needed %s values" % (name, valList, numElts,))
    valStr = ",".join([valFmt % (val,) for val in valList])
    return "%s=%s" % (name, valStr)

if __name__ == "__main__":
    for actor in _InstInfoDict:
        getModel(actor)
