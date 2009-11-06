#!/usr/bin/env python
"""Exposure input (data entry) widget.

History:
2003-04-24 ROwen
2003-05-06 ROwen    Modified to use 2003-05-06 Gridder.
2003-07-10 ROwen    Modified to use overhauled RO.InputCont
2003-07-25 ROwen    Added manual/auto sequence #; improved test code
2003-07-30 ROwen    Modified to be generic for all instruments and to use Inst.ExposeModel
2003-08-01 ROwen    Changed sequence number handling to use Share Seq instead of auto/man.
2003-08-04 ROwen    Added Cameras widget
2003-08-08 ROwen    Fixed output from Cameras widget.
2003-08-15 ROwen    Beginning of auto ftp support
2003-09-22 ROwen    Added auto ftp support
2003-09-30 ROwen    Updated the help prefix.
2003-10-01 ROwen    Stopped stripping leading slashes from file name; no longer needed.
2003-10-06 ROwen    Modified to use new hub (new versions of files and nextPath).
2003-10-16 ROwen    Bug fix: had not removed inst=<inst> from expose command data;
                    also, was not ignoring files named None.
2003-10-20 ROwen    Modified to use min exposure time.
2003-10-22 ROwen    Modified to put #Exp on its own line; it was too hard to see.
2003-11-17 ROwen    Modified to use modified RO.Wdg.StrEntry
                    (partialPattern instead of validPattern).
2003-12-05 ROwen    Modified for RO.Wdg.Entry changes.
2004-01-29 ROwen    Bug fix: the most recent files are (re)transferred on refresh;
                    fixed by not messing with timer for data from the cache.
2004-05-18 ROwen    Bug fix: code referred to self.autoFTPPref, which did not exist.
                    Stopped importing ftplib and re; they weren't used.
                    Ditched constants _AutoSeqCat and _ManSeqCat; they weren't used.
2004-08-13 ROwen    Modified to only auto-ftp if widget visible.
                    Modified to update expNum when first constructed (to help scripts).
2004-09-01 ROwen    Modified to use program/date subdir when saving via auto ftp.
                    Bug fix: if user tried to deselect all cameras,
                    the last camera deselected was re-selected but did not display that way.
2004-09-16 ROwen    Moved auto ftp handling into ExposeModel.
                    Changed controls for sequence # and auto ftp into read-only widgets;
                    use preferences to control these (this makes scripts work better).
                    Modified getString to use the new expose model's formatExpCmd
                    and added some arguments for use in scripts.
                    Modified columnconfigure to make use in scripts easier.
2004-09-23 ROwen    Moved prefs display to ExposeStatusWdg.
2005-07-13 ROwen    Modified getString to test for an empty time field,
                    so we can tell the difference between an empty field and 0).
2005-07-21 ROwen    Bug fix (APO PR 224): non-blank time required for bias exposure.
                    Changed file name label from Name to File Name
                    and added a subdirectory hint to the help text.
2005-09-15 ROwen    Moved prefs wdgs back here, since users can set them again.
                    Prefs are now Auto Get, View Image and More....
2006-04-14 ROwen    Added explicit default to typeWdgSet (required
                    due to recent changes in RO.Wdg.RadiobuttonSet).
2007-07-02 ROwen    Added helpURL argument.
2008-04-29 ROwen    Fixed reporting of exceptions that contain unicode arguments.
2008-11-07 ROwen    Added bin, window and overscan support; this presently includes support for
                    zero or one-based window and one or two-component bin factor
                    but depending on changes in the hub some of these features may be removed.
2009-02-26 ROwen    Added Full button to set full window.
                    Bug fix: max window value not updated when bin factor changed.
2009-11-05 ROwen    Modified to use TUI.TUIMenu.PreferencesWindow.WindowName.
"""
import Tkinter
import RO.InputCont
import RO.SeqUtil
import RO.StringUtil
import RO.Wdg
import ExposeModel
import TUI.TUIMenu.PreferencesWindow

# magic numbers
_MaxNumExp = 9999

_HelpURL = "Instruments/ExposeWin.html"

class ExposeInputWdg (Tkinter.Frame):
    def __init__(self,
        master,
        instName,
        expTypes = None, # override default
        helpURL = None,
    **kargs):
        #print "ExposeInputWdg(%r, %r, %r)" % (master, instName, expTypes)

        Tkinter.Frame.__init__(self, master, **kargs)
        if helpURL == None:
            helpURL = _HelpURL
        
        self.entryError = None
        self.wdgAreSetUp = False        
        self.expModel = ExposeModel.getModel(instName)
        self.WindowCat = "window"
        self.currUnbWindow = [0, 0, 0, 0]
        self.updatingBin = False
        self.binsMatch = True
        
        gr = RO.Wdg.Gridder(self, sticky="w")
        self.gridder = gr

        prefFrame = Tkinter.Frame(self)
        
        self.autoGetWdg = RO.Wdg.Checkbutton (
            master = prefFrame,
            text = "Auto Get",
            var = self.expModel.autoGetVar,
            helpURL = helpURL,
            helpText = "Automatically download %s images?" % (self.expModel.instName,),
        )
        self.autoGetWdg.pack(side="left")

        self.viewImageWdg = RO.Wdg.Checkbutton (
            master = prefFrame,
            text = "View Image",
            var = self.expModel.viewImageVar,
            helpURL = helpURL,
            helpText = "View downloaded %s images in ds9?" % (self.expModel.instName,),
        )
        self.viewImageWdg.pack(side="left")
        self.autoGetWdg.addCallback(self.autoGetToggled, callNow=True)

        self.prefsTL = self.expModel.tuiModel.tlSet.getToplevel(TUI.TUIMenu.PreferencesWindow.WindowName)
        if self.prefsTL:
            showPrefsBtn = RO.Wdg.Button(
                master = prefFrame,
                text = "More...",
                callFunc = self.showExposurePrefs,
                helpText = "show global exposure prefs",
                helpURL = helpURL,
            )
            showPrefsBtn.pack(side="left")
        #else:
            #prefsWdg = RO.Wdg.StrLabel(
                #master = self,
                #text = "Prefs",
            #)
        
        gr.gridWdg("Prefs", prefFrame, colSpan=5, sticky="w")

        typeFrame = Tkinter.Frame(self)
        if expTypes != None:
            expTypes = RO.SeqUtil.asSequence(expTypes)
        else:
            expTypes = self.expModel.instInfo.expTypes
        expTypeLabels = [name.capitalize() for name in expTypes]
        
        self.typeWdgSet = RO.Wdg.RadiobuttonSet (
            master = typeFrame,
            textList = expTypeLabels,
            valueList = expTypes,
            defValue = expTypes[0],
            command = self._handleType,
            side = "left",
            helpText = "Type of exposure",
            helpURL = helpURL,
        )
        if len(expTypes) > 1:
            gr.gridWdg("Type", typeFrame, colSpan=5, sticky="w")

        timeUnitsVar = Tkinter.StringVar()
        self.timeWdg = RO.Wdg.DMSEntry (self,
            minValue = self.expModel.instInfo.minExpTime,
            maxValue = self.expModel.instInfo.maxExpTime,
            isRelative = True,
            isHours = True,
            unitsVar = timeUnitsVar,
            width = 10,
            minMenu = "Minimum",
            maxMenu = "Maximum",
            helpText = "Exposure time",
            helpURL = helpURL,
        )
        wdgSet = gr.gridWdg("Time", self.timeWdg, timeUnitsVar)
        self.timeWdgSet = wdgSet.wdgSet
        
        self.numExpWdg = RO.Wdg.IntEntry(self,
            defValue = 1,
            minValue = 1,
            maxValue = _MaxNumExp,
            defMenu = "Minimum",
            helpText = "Number of exposures in the sequence",
            helpURL = helpURL,
        )
        gr.gridWdg("#Exp", self.numExpWdg) #, row=-1, col=4)
        self.grid_columnconfigure(5, weight=1)
        
        self.camWdgs = []
        camNames = self.expModel.instInfo.camNames
        if len(camNames) > 1:
            cnFrame = Tkinter.Frame(self)
            for camName in camNames:
                wdg = RO.Wdg.Checkbutton(
                    cnFrame,
                    text = camName.capitalize(),
                    callFunc = self._camSelect,
                    defValue = True,
                    helpText = "Save data from %s camera" % (camName.lower()),
                    helpURL = helpURL,
                )
                self.camWdgs.append(wdg)
                wdg.pack(side="left")
            gr.gridWdg("Cameras", cnFrame, colSpan=5, sticky="w")

        self.binWdgSet = []
        binWdgFrame = Tkinter.Frame(self)
        if self.expModel.instInfo.numBin > 0:
            if self.expModel.instInfo.numBin == 1:
                helpStrList = ("bin factor (x = y)", )
            elif self.expModel.instInfo.numBin == 2:
                helpStrList = ("x bin factor", "y bin factor")
            else:
                raise RuntimeError("Invalid expModel.instInfo.numBin=%s" % (self.expModel.instInfo.numBin,))
            for ind, helpStr in enumerate(helpStrList):
                binWdg = RO.Wdg.IntEntry(
                    binWdgFrame,
                    defValue = self.expModel.instInfo.defBin[ind],
                    minValue = 1,
                    callFunc = self._updBinFactor,
                    width = 4,
                    defMenu = "Default",
                    minMenu = "Minimum",
                    helpText = helpStr,
                    helpURL = helpURL,
                )
                self.binWdgSet.append(binWdg)
                binWdg.pack(side="left")
            gr.gridWdg("Bin Factor", binWdgFrame, colSpan=5)

        self.windowWdgSet = []
        minWindow = 1
        self.overscanWdgSet = []
        if self.expModel.instInfo.canWindow:
            self.showWindowBtn = RO.Wdg.Checkbutton(
                self,
                text = "Image Size",
                indicatoron = False,
                helpText = "show/hide image size controls",
                helpURL = helpURL,
            )
            self.imageSizeWdg = RO.Wdg.StrLabel(
                self,
                helpText = "image size: x (+overscan) by y (+overscan) (binned pixels)",
                helpURL = helpURL,
            )
            gr.gridWdg(self.showWindowBtn, self.imageSizeWdg, colSpan=5)
            gr.addShowHideControl(self.WindowCat, self.showWindowBtn)
            
            windowWdgFrame = Tkinter.Frame(self)
            maxWindowList = [minWindow + self.expModel.instInfo.imSize[ind] - 1 for ind in (0, 1, 0, 1)]
            for ind, helpStr in enumerate(("x begin", "y begin", "x end", "y end")):
                windowWdg = RO.Wdg.IntEntry(
                    windowWdgFrame,
                    minValue = minWindow,
                    maxValue = maxWindowList[ind],
                    defValue = (minWindow if ind < 2 else maxWindowList[ind]),
                    defMenu = "Default",
                    callFunc = self._updWindow,
                    helpText = helpStr + " (binned pixels)",
                    helpURL = helpURL,
                )
                self.windowWdgSet.append(windowWdg)
                windowWdg.pack(side = "left")
            self.fullWindowWdg = RO.Wdg.Button(
                windowWdgFrame,
                text = "Full",
                callFunc = self._doFullWindow,
                helpText = "Set full window",
                helpURL = helpURL,
            )
            self.fullWindowWdg.pack(side="left")
            gr.gridWdg("Window", windowWdgFrame, colSpan=5, cat=self.WindowCat)
            
            if self.expModel.instInfo.defOverscan:
                overscanWdgFrame = Tkinter.Frame(self)
                for ii, helpStr in enumerate(("x overscan", "y overscan")):
                    overscanWdg = RO.Wdg.IntEntry(
                        overscanWdgFrame,
                        minValue = 0,
                        defValue = self.expModel.instInfo.defOverscan[ii],
                        defMenu = "Current",
                        width = 4,
                        callFunc = self._updImageSize,
                        helpText = helpStr + " (binned pixels)",
                        helpURL = helpURL,
                    )
                    self.overscanWdgSet.append(overscanWdg)
                    overscanWdg.pack(side="left")
                gr.gridWdg("Overscan", overscanWdgFrame, colSpan=5, cat=self.WindowCat)
            self._updWindow()
        
        self.fileNameWdg = RO.Wdg.StrEntry(
            master = self,
            helpText = "File name or subdirectory/name",
            helpURL = helpURL,
            partialPattern = r"^[-_./a-zA-Z0-9]*$",
        )
        gr.gridWdg("File Name", self.fileNameWdg, colSpan=5, sticky="ew")
                
        self.commentWdg = RO.Wdg.StrEntry(
            master = self,
            helpText = "Comment (saved in the FITS header)",
            helpURL = helpURL,
        )
        gr.gridWdg("Comment", self.commentWdg, colSpan=5, sticky="ew")

        gr.allGridded()

        self.wdgAreSetUp = True
    
    def autoGetToggled(self, wdg=None):
        doAutoGet = self.autoGetWdg.getBool()
        self.viewImageWdg.setEnable(doAutoGet)

    def getEntryError(self):
        return self.entryError
    
    def getExpType(self):
        return self.typeWdgSet.getString()

    def getString(self, numExp=None, startNum=None, totNum=None):
        """Return the current exposure command, or None on error.
        
        On error (inputs are missing or invalid),
        display a suitable error message and return None.
        """
        try:
            if self.timeWdg.getString() == "":
                expTime = None
            else:
                expTime = self.timeWdg.getNum()
            camList = [wdg["text"].lower() for wdg in self.camWdgs if wdg.getBool()]
            return self.expModel.formatExpCmd(
                expType = self.typeWdgSet.getString(),
                expTime = expTime,
                cameras = camList,
                fileName = self.fileNameWdg.getString(),
                numExp = numExp or self.numExpWdg.getNum(),
                bin = [wdg.getNum() for wdg in self.binWdgSet],
                window = [wdg.getNum() for wdg in self.windowWdgSet],
                overscan = [wdg.getNum() for wdg in self.overscanWdgSet],
                comment = self.commentWdg.getString(),
                startNum = startNum,
                totNum = totNum,
            )
        except (ValueError, TypeError), e:
            self._setEntryError(RO.StringUtil.strFromException(e))
            return None
    
    def showExposurePrefs(self, wdg=None):
        """Show Exposures panel of Preferences window"""
        if not self.prefsTL:
            return

        prefsWdg = self.prefsTL.getWdg()
        self.prefsTL.makeVisible()
        prefsWdg.showCategory("Exposures")
    
    def _doFullWindow(self, wdg=None):
        """Set window controls to full window"""
        for wdg in self.windowWdgSet:
            wdg.restoreDefault()
    
    def _camSelect(self, wdg=None):
        """Called whenever a camera is selected.
        Makes sure at least one camera is always selected.
        """
        anySelected = False
        for awdg in self.camWdgs:
            if awdg.getBool():
                anySelected = True
                break
        if not anySelected:
            wdg.after(1, wdg.select)
            wdg.bell()
            self._setEntryError("at least one camera must be selected")

    def _handleType(self):
        """Enables or disables the time input widget
        depending on the type of exposure.
        """
        expType = self.typeWdgSet.getString()
        if expType == "bias":
            for wdg in self.timeWdgSet:
                wdg["state"] = "disabled"
        else:
            for wdg in self.timeWdgSet:
                wdg["state"] = "normal"
    
    def _setEntryError(self, errMsg):
        self.entryError = errMsg
        self.event_generate("<<EntryError>>")
    
    def _updBinFactor(self, wdg):
        """Bin factor changed; update window"""
        if wdg.getNum() == 0:
            return
        if not self.windowWdgSet:
            return
        if self.updatingBin:
            return
        #print "_updBinFactor"
            
        if len(self.binWdgSet) == 2 and wdg == self.binWdgSet[0] and self.binsMatch:
            # user changed x bin, and x=y before the change so update y to match
            try:
                self.updatingBin = True
                self.binWdgSet[1].set(self.binWdgSet[0].getNum())
            finally:
                self.updatingBin = False

        try:
            self.updatingBin = True
            
            bin = [wdg.getNum() for wdg in self.binWdgSet]
            if len(bin) == 1:
                bin2 = [bin[0], bin[0]]
            else:
                bin2 = bin
            newWindow = self.expModel.imageWindow.binWindow(self.currUnbWindow, bin2)
            for ind, wdg in enumerate(self.windowWdgSet[:2]):
                wdg.set(newWindow[ind])
            newFullWindowUR = self.expModel.imageWindow.getFullBinWindow(bin2)[2:]
            for ind, wdg in enumerate(self.windowWdgSet[2:]):
                # first set value and default to 1, then update range, then set proper value and default
                # to avoid complaints about invalid values
                wdg.setDefault(1)
                wdg.set(1)
                wdg.setRange(1, newFullWindowUR[ind])
                wdg.setDefault(newFullWindowUR[ind])
                wdg.set(newWindow[2:][ind])
            self.binsMatch = (bin2[0] == bin2[1])
        finally:
            self.updatingBin = False
        self._updImageSize()

    def _updImageSize(self, wdg=None):
        """Window or overscan changed; update image size"""
        if self.updatingBin:
            return
        #print "_updImageSize"
        window = [wdg.getNum() for wdg in self.windowWdgSet]
        overscan = [wdg.getNum() for wdg in self.overscanWdgSet]
        size = [1 + window[ii+2] - window[ii] for ii in range(2)]
        overscanStrs = [" + %d" % (val,) if val > 0 else "" for val in overscan]
        strSize = "%d%s x %d%s" % (size[0], overscanStrs[0], size[1], overscanStrs[1])
        self.imageSizeWdg.set(strSize)
   
    def _updWindow(self, wdg=None):
        """Window changed; update currUnbWindow and image size"""
        if self.updatingBin:
            return
        window = [wdg.getNum() for wdg in self.windowWdgSet]
        #print "_updWindow; window=", window
        bin = [wdg.getNum() for wdg in self.binWdgSet]
        if len(bin) == 1:
            bin2 = [bin[0], bin[0]]
        else:
            bin2 = bin
        self.currUnbWindow = self.expModel.imageWindow.unbinWindow(window, bin2)
        fullWindow = self.expModel.imageWindow.getFullBinWindow(bin2)
        isFullWindow = list(fullWindow) == window
        self.fullWindowWdg.setEnable(not isFullWindow)
        self._updImageSize()
        
        

if __name__ == '__main__':
    root = RO.Wdg.PythonTk()
    root.resizable(width=False, height=False)

    import ExposeTestData
    
    def printCmd():
        print testFrame.getString()

    testFrame = ExposeInputWdg(root, "DIS")
    testFrame.pack(side="top", expand="yes", fill="x")
    testFrame.timeWdg.set(1)
    testFrame.fileNameWdg.set("test")
    
    bf = Tkinter.Frame()
    Tkinter.Button (bf, command=printCmd, text="Print Cmd").pack(side="left")

    Tkinter.Button(bf, text="Demo", command=ExposeTestData.animate).pack(side="left")
    bf.pack(side="top")

    ExposeTestData.dispatch()

    root.mainloop()
