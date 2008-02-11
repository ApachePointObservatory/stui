#!/usr/bin/env python
"""Configuration input panel for Dual Imaging Spectrograph.

To Do:
- verify that a value will be changed if and only if a widget is not current;
  it may be worth recoding containers to implement this.
  (It probably works now, but I'd rather be certain!).
- add a binning menu of common choices?
- make window wide enough that changing the turret position doesn't change the window width (how? by setting menu bar width?)

History:
2003-03-10 ROwen    Preliminary attempt. Lots to do.
2003-03-11 ROwen    Added mask, filter and turret menus (after overhauling RO.Wdg.OptionMenu)
2003-03-14 ROwen    Added command list retrieval; wired up the lambda widgets correctly.
2003-03-17 ROwen    Improved layout and units labelling; mod. for new keywords.
2003-03-19 ROwen    Mod. to use model.turretNames instead of Model.TurretPosDict
2003-03-24 ROwen    Made window and overscan into hideable details;
                    modified to use Model.getModel().
2003-03-31 ROwen    Modified to use RO.Wdg.Gridder; cleaned up widths and sticky;
                    changed so motor commands are sent one at a time instead of all at once
                    so they can be cancelled partway through.
2003-04-03 ROwen    Bug fix: the previous change broke doClear;
                    mod. to require all fields for bin, window and overscan.
2003-04-16 ROwen    Combined status and config widgets.
2003-04-17 ROwen    Improved show/hide buttons; fixed bug showing unwanted config widgets.
2003-04-22 ROwen    Changed the help URL to point to the new combo status/config doc.
2003-05-08 ROwen    Added more helpText strings.
2003-06-09 ROwen    Removed most args from StatusConfiInputWdg.__init__.
2003-06-13 ROwen    Removed defIfDisabled (wasn't doing anything).
2003-07-03 ROwen    Mod. to restore defaults whenever config widgets
                    are shown; this fixes a bug whereby the entry boxes
                    were blank until "Current" was pressed.
2003-07-10 ROwen    Modified to use overhauled RO.InputCont.
2003-08-07 ROwen    Made initial status items full width;
                    this improves display of invalid data state.
2003-08-11 ROwen    Modified to use enhanced Gridder.
2003-10-16 ROwen    Modified window to be in binned pixels (a major change);
                    mod. to update ccd window entry limits as bin factor changed;
                    added image size;
                    added support for new model.cmdLambda, fixing a cosmetic bug.
2003-12-04 ROwen    Modified to handle window size of None
2003-12-05 ROwen    Modified for RO.Wdg.Entry changes.
2004-05-18 ROwen    Removed constant _CfgCol; it wasn't used.
2004-08-11 ROwen    Use modified RO.Wdg state constants with st_ prefix.
2004-09-03 ROwen    Modified for RO.Wdg.st_... -> RO.Constants.st_...
2004-09-23 ROwen    Modified to allow callNow as the default for keyVars.
2004-11-15 ROwen    Modified to use RO.Wdg.Checkbutton's improved defaults.
2005-01-04 ROwen    Modified to use autoIsCurrent for input widgets.
                    Corrected minimum bin factor; was 0, is now 1.
2005-01-05 ROwen    Modified for RO.Wdg.Label state->severity and RO.Constants.st_... -> sev...
2005-06-08 ROwen    Changed indFormat to a new-style class.
2006-04-27 ROwen    Removed use of ignored clearMenu and defMenu in StatusConfigGridder.
2006-10-20 ROwen    Modified to use new RO.Wdg.OptionMenu index method to avoid tk misfeature.
2008-02-11 ROwen    Modified to be compatible with the new TUI.Inst.StatusConfigWdg.
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import DISModel

_MaxDataWidth = 5

_ColWidth = 6   # width of data columns for red/blue or x/y data

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
    InstName = "DIS"
    HelpPrefix = 'Instruments/%s/%sWin.html#' % (InstName, InstName)

    # control show/hide categories
    ConfigCat = RO.Wdg.StatusConfigGridder.ConfigCat
    DetailCat = "detail"
    CCDCat = "ccd"
    GSCat = {1:"gset1", 2:"gset2"}
    
    def __init__(self,
        master,
    **kargs):
        """Create a new widget to show status for and configure the Dual Imaging Spectrograph
        """
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        self.model = DISModel.getModel()

        # set while updating user ccd binning or user window default,
        # to prevent storing new unbinned values for ccd window.        
        self._freezeCCDUBWindow = False
        
        gr = RO.Wdg.StatusConfigGridder(
            master = self,
            sticky = "e",
        )
        self.gridder = gr

        shutterCurrWdg = RO.Wdg.StrLabel(self,
            helpText = "current state of the shutter",
            helpURL = self.HelpPrefix + "Shutter",
            anchor = "w",
        )
        self.model.shutter.addROWdg(shutterCurrWdg)
        gr.gridWdg ("Shutter", shutterCurrWdg, sticky="ew", colSpan=3)

        # generate turret index dict: key=turret name, value=turret pos
        turretNames = self.model.turretNames.get()[0]
        self.turretIndexDict = {}
        for ii in range(len(turretNames)):
            self.turretIndexDict[turretNames[ii]] = ii+1
        def getTurretIndex(turretName):
            return self.turretIndexDict.get(turretName)

        
        maskNameCurrWdg = RO.Wdg.StrLabel(self,
            helpText = "current slit mask",
            helpURL = self.HelpPrefix + "Mask",
            anchor = "w",
        )
        self.model.maskName.addROWdg(maskNameCurrWdg)

        self.maskNameUserWdg = RO.Wdg.OptionMenu(self,
            items=[],
            helpText = "requested slit mask",
            helpURL = self.HelpPrefix + "Mask",
            defMenu = "Current",
            autoIsCurrent = True,
        )
#       self.model.maskNames.addCallback(self.maskNameUserWdg.setItems)
#       self.model.maskName.addIndexedCallback(self.maskNameUserWdg.setDefault, 0)
        gr.gridWdg (
            label = "Mask",
            dataWdg = maskNameCurrWdg,
            units = False,
            cfgWdg = self.maskNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        filterNameCurrWdg = RO.Wdg.StrLabel(self,
            helpText = "current filter set",
            helpURL = self.HelpPrefix + "Filter",
            anchor = "w",
        )
        self.model.filterName.addROWdg(filterNameCurrWdg)
        self.filterNameUserWdg = RO.Wdg.OptionMenu(self,
            items=[],
            helpText = "requested filter set",
            helpURL = self.HelpPrefix + "Filter",
            defMenu = "Current",
            autoIsCurrent = True,
        )
#       self.model.filterNames.addCallback(self.filterNameUserWdg.setItems)
#       self.model.filterName.addIndexedCallback(self.filterNameUserWdg.setDefault, 0)
        gr.gridWdg (
            label = "Filter",
            dataWdg = filterNameCurrWdg,
            units = False,
            cfgWdg = self.filterNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )

        self.turretNameCurrWdg = RO.Wdg.StrLabel(self,
            helpText = "current pos. of grating turret",
            helpURL=self.HelpPrefix + "Turret",
            anchor = "w",
        )
#       self.model.turretName.addIndexedCallback(self._doTurretName, 0)

        turretNames = self.model.turretNames.get()[0]
        turretNames.insert(3, None)
        self.turretNameUserWdg = RO.Wdg.OptionMenu(self,
            items=turretNames,
            callFunc=self._showHideGratingWdg,
            helpText = "requested pos. of grating turret",
            helpURL = self.HelpPrefix + "Turret",
            defMenu = "Current",
            autoIsCurrent = True,
        )
#       self.model.turretName.addIndexedCallback(self.turretNameUserWdg.setDefault, 0)
        gr.gridWdg (
            label = "Turret",
            dataWdg = self.turretNameCurrWdg,
            units = False,
            cfgWdg = self.turretNameUserWdg,
            sticky = "ew",
            cfgSticky = "w",
            colSpan = 3,
        )
        
        # give the last column weight 1
        # so all other columns shrink as small as possible
        lastCol = gr.getNextCol() - 1
        self.columnconfigure(lastCol, weight=1)

        frame = Tkinter.Frame(self)
        detentCurrWdg = RO.Wdg.StrLabel(frame,
            helpText = "commanded pos. of turret detent",
            helpURL = self.HelpPrefix + "Detent",
        )
        detentCurrWdg.pack(side="left")
        Tkinter.Label(frame, text="steps").pack(side="left")
        self.model.detent.addROWdg(detentCurrWdg)
        gr.gridWdg (
            label = "Detent",
            dataWdg = frame,
            sticky = "w",
            colSpan = 3,
            cat = self.DetailCat,
        )

        # color-specific widgets
        
        colorDescr = (
            "blue",
            "red",
        )
        
        # color header; the label is a toggle button
        # for showing details (because most details
        # are color-specific and for lack of a better place)
        self.showDetailWdg = RO.Wdg.Checkbutton(self,
            onvalue = "Show Less",
            offvalue = "Show More",
            defValue = False,
            showValue = True,
            helpText = "show/hide engineering details",
            helpURL = self.HelpPrefix + "ShowMore",
        )
        gr.addShowHideControl(self.DetailCat, self.showDetailWdg)

        colorLabelDict = {}
        for setName in ("data", "cfg"):
            colorLabelDict[setName] = [
                Tkinter.Label(self,
                    text=colorName,
                    width=_MaxDataWidth,
                    anchor="e",
                ) for colorName in ("Blue", "Red")
            ]
        gr.gridWdg (
            label = self.showDetailWdg,
            dataWdg = colorLabelDict["data"],
            cfgWdg = colorLabelDict["cfg"],
            sticky = "",
        )

        # grating status; grid this first,
        # then two sets of grating cfg widgets (one per grating set)
        # treat other configurable grating-specific items the same way
        gratingCurrWdgSet = [
            RO.Wdg.StrLabel(self,
                width = _ColWidth,
                anchor = "e",
                helpText = "current %s grating" % colorDescr[ii],
                helpURL=self.HelpPrefix + "Grating",
            )
            for ii in range(2)
        ]
        self.model.gratings.addROWdgSet(gratingCurrWdgSet)
        gr.gridWdg(
            label = "Grating",
            dataWdg = gratingCurrWdgSet,
        )
        
        # grating name config (read only); two sets, one per grating set
        for gsid in (1,2):
            gratingWdgSet = [
                RO.Wdg.StrLabel(self,
                    width = _MaxDataWidth,
                    anchor="e",
                    helpText = "requested %s grating" % colorDescr[ii],
                    helpURL = self.HelpPrefix + "Grating",
                )
                for ii in range(2)
            ]
            gr.gridWdg (
                label = None,
                dataWdg = [None, None],
                cfgWdg = gratingWdgSet,
                cat = self.GSCat[gsid],
                row = -1,
            )
            self.model.gratingsByGSID.getKeyVarByID(gsid).addROWdgSet(gratingWdgSet)

        # dispersion status
        dispersionCurrWdgSet = [
            RO.Wdg.StrLabel(self,
                width = _ColWidth,
                anchor = "e",
                helpText = "dispersion of current %s grating" % colorDescr[ii],
                helpURL = self.HelpPrefix + "Dispersion",
            )
            for ii in range(2)
        ]
        self.model.dispersions.addROWdgSet(dispersionCurrWdgSet)
        gr.gridWdg(
            label = "Dispersion",
            dataWdg = dispersionCurrWdgSet,
            units = u"\u00c5/pix",
        )

        # dispersion config (read only display)
        for gsid in (1,2):
            dispersionWdgSet = [
                RO.Wdg.StrLabel(self,
                    width = 4,
                    anchor="e",
                    helpText = "dispersion of requested %s grating" % colorDescr[ii],
                    helpURL = self.HelpPrefix + "Dispersion",
                )
                for ii in range(2)
            ]
            gr.gridWdg (
                label = None,
                dataWdg = [None, None],
                cfgWdg = dispersionWdgSet,
                cfgUnits = u"\u00c5/pix",
                cat = self.GSCat[gsid],
                row = -1,
            )
            self.model.dispersionsByGSID.getKeyVarByID(gsid).addROWdgSet(dispersionWdgSet)
        
        # current lambda
        lambdaCurrWdgSet = [
            RO.Wdg.IntLabel(self,
                width = _ColWidth,
                anchor = "e",
                helpText = "central wavelength of %s grating" % colorDescr[ii],
                helpURL = self.HelpPrefix + "Lambda",
            )
            for ii in range(2)
        ]       
        self.model.actLambdas.addROWdgSet(lambdaCurrWdgSet)
        gr.gridWdg(
            label = u"\u03BB",
            dataWdg = lambdaCurrWdgSet,
            units = u"\u00c5",
        )

        # user-set lambda
        self.lambdaUserWdgSet = {}
        maxLambda = (9999, 19999)
        for gsid in (1,2):
            self.lambdaUserWdgSet[gsid] = [
                RO.Wdg.IntEntry(self,
                    minValue = 0,
                    maxValue = maxLambda[ii],
                    width = 5,
                    helpText = "central wavelength of %s grating" % colorDescr[ii],
                    helpURL = self.HelpPrefix + "Lambda",
                    clearMenu = None,
                    defMenu = "Current",
                    autoIsCurrent = True,
                ) for ii in range(2)
            ]
            self.model.cmdLambdasByGSID.getKeyVarByID(gsid).addROWdgSet(
                self.lambdaUserWdgSet[gsid], setDefault=True)
            gr.gridWdg (
                label = None,
                dataWdg = [None, None],
                cfgWdg = self.lambdaUserWdgSet[gsid],
                cfgUnits = u"\u00c5",
                cat = self.GSCat[gsid],
                row = -1,
            )

        # color-specific detail widgets (all status-only)

        zeroCurrWdgSet = [
            RO.Wdg.IntLabel(self,
                width = _ColWidth,
                anchor = "e",
                helpText = "tilt of %s grating at lambda = 0" % colorDescr[ii],
                helpURL=self.HelpPrefix + "ZeroTilt",
            )
            for ii in range(2)
        ]
        self.model.zeroSteps.addROWdgSet(zeroCurrWdgSet)
        gr.gridWdg(
            label = "Zero Tilt",
            dataWdg = zeroCurrWdgSet,
            units = "steps",
            cat = self.DetailCat,
        )

        tiltCurrWdgSet = [
            RO.Wdg.IntLabel(self,
                width = _ColWidth,
                anchor = "e",
                helpText = "tilt of %s grating at current lambda" % colorDescr[ii],
                helpURL=self.HelpPrefix + "Tilt",
            )
            for ii in range(2)
        ]
        self.model.steps.addROWdgSet(tiltCurrWdgSet)
        gr.gridWdg(
            label = "Tilt",
            dataWdg = tiltCurrWdgSet,
            units = "steps",
            cat = self.DetailCat,
        )

        ccdTempsCurrWdgSet = [
            RO.Wdg.StrLabel(self,
                width = _ColWidth,
                anchor = "e",
                helpText = "current temperature of %s CCD" % colorDescr[ii],
                helpURL=self.HelpPrefix + "Temp",
            )
            for ii in range(2)
        ]
        self.model.ccdTemps.addROWdgSet(ccdTempsCurrWdgSet)
        gr.gridWdg(
            label = "Temp",
            dataWdg = ccdTempsCurrWdgSet,
            units = "C",
            cat = self.DetailCat,
        )

        ccdHeatersCurrWdgSet = [
            RO.Wdg.StrLabel(self,
                width = _ColWidth,
                anchor = "e",
                helpText = "heater current (%% of full) for %s CCD" % colorDescr[ii],
                helpURL=self.HelpPrefix + "Heater",
            )
            for ii in range(2)
        ]
        self.model.ccdHeaters.addROWdgSet(ccdHeatersCurrWdgSet)
        gr.gridWdg(
            label = "Heater",
            dataWdg = ccdHeatersCurrWdgSet,
            units = "%",
            cat = self.DetailCat,
        )

        # ccd widgets
        
        # store user-set window in unbinned pixels
        # so the displayed binned value can be properly
        # updated when the user changes the binning
        self.userCCDUBWindow = None
        
        # ccd image header; the label is a toggle button
        # for showing ccd image info
        # grid that first as it is always displayed
        self.showCCDWdg = RO.Wdg.Checkbutton(self,
            onvalue = "Hide CCD",
            offvalue = "Show CCD",
            defValue = False,
            showValue = True,
            helpText = "show/hide binning, etc.",
            helpURL = self.HelpPrefix + "ShowCCD",
        )
        gr.addShowHideControl(self.CCDCat, self.showCCDWdg)
        gr.gridWdg (
            label = self.showCCDWdg,
        )
        
        # grid ccd labels; these show/hide along with all other CCD data
        ccdLabelDict = {}
        for setName in ("data", "cfg"):
            ccdLabelDict[setName] = [
                Tkinter.Label(self,
                    text=axis,
                )
                for axis in (u"x(\u03BB)", "y")
            ]
        gr.gridWdg (
            label = None,
            dataWdg = ccdLabelDict["data"],
            cfgWdg = ccdLabelDict["cfg"],
            sticky = "e",
            cat = self.CCDCat,
            row = -1,
        )
        
        ccdDescr = (
            "x (dispersion)",
            "y",
        )

        ccdBinCurrWdgSet = [RO.Wdg.IntLabel(self,
            width = 4,
            helpText = "current bin factor in %s" % ccdDescr[ii],
            helpURL=self.HelpPrefix + "Bin",
        )
            for ii in range(2)
        ]
        self.model.ccdBin.addROWdgSet(ccdBinCurrWdgSet)
        
        self.ccdBinUserWdgSet = [
            RO.Wdg.IntEntry(self,
                minValue = 1,
                maxValue = 99,
                width = 2,
                helpText = "requested bin factor in %s" % ccdDescr[ii],
                helpURL = self.HelpPrefix + "Bin",
                clearMenu = None,
                defMenu = "Current",
                callFunc = self._userBinChanged,
                autoIsCurrent = True,
            )
            for ii in range(2)
        ]       
        self.model.ccdBin.addROWdgSet(self.ccdBinUserWdgSet, setDefault=True)
        gr.gridWdg (
            label = "Bin",
            dataWdg = ccdBinCurrWdgSet,
            cfgWdg = self.ccdBinUserWdgSet,
            cat = self.CCDCat,
        )

        # CCD window

        winDescr = (
            "smallest x",
            "smallest y",
            "largest x",
            "largest y",
        )
        ccdWindowCurrWdgSet = [RO.Wdg.IntLabel(self,
            width = 4,
            helpText = "%s of current window (binned pix)" % winDescr[ii],
            helpURL = self.HelpPrefix + "Window",
        )
            for ii in range(4)
        ]
        self.model.ccdWindow.addROWdgSet(ccdWindowCurrWdgSet)
        
        self.ccdWindowUserWdgSet = [
            RO.Wdg.IntEntry(self,
                minValue = 1,
                maxValue = (2048, 1028, 2048, 1028)[ii],
                width = 4,
                helpText = "%s of requested window (binned pix)" % winDescr[ii],
                helpURL = self.HelpPrefix + "Window",
                clearMenu = None,
                defMenu = "Current",
                minMenu = ("Mininum", "Minimum", None, None)[ii],
                maxMenu = (None, None, "Maximum", "Maximum")[ii],
                callFunc = self._userWindowChanged,
                autoIsCurrent = True,
                isCurrent = False,
            ) for ii in range(4)
        ]
#       self.model.ccdUBWindow.addCallback(self._setCCDWindowWdgDef)
        wdgSet = gr.gridWdg (
            label = "Window",
            dataWdg = ccdWindowCurrWdgSet[0:2],
            cfgWdg = self.ccdWindowUserWdgSet[0:2],
            units = "LL bpix",
            cat = self.CCDCat,
        )
        gr.gridWdg (
            label = None,
            dataWdg = ccdWindowCurrWdgSet[2:4],
            cfgWdg = self.ccdWindowUserWdgSet[2:4],
            units = "UR bpix",
            cat = self.CCDCat,
        )

        # Image size, in binned pixels
        self.ccdImageSizeCurrWdgSet = [RO.Wdg.IntLabel(self,
            width = 4,
            helpText = "current %s size of image (binned pix)" % winDescr[ii],
            helpURL = self.HelpPrefix + "Window",
        )
            for ii in range(2)
        ]
#       self.model.ccdWindow.addCallback(self._updCurrImageSize)
        
        self.ccdImageSizeUserWdgSet = [
            RO.Wdg.IntLabel(self,
                width = 4,
                helpText = "requested %s size of image (binned pix)" % ("x", "y")[ii],
                helpURL = self.HelpPrefix + "ImageSize",
            ) for ii in range(2)
        ]
        wdgSet = gr.gridWdg (
            label = "Image Size",
            dataWdg = self.ccdImageSizeCurrWdgSet,
            cfgWdg = self.ccdImageSizeUserWdgSet,
            units = "bpix",
            cat = self.CCDCat,
        )

        # ccd overscan
        ccdOverscanCurrWdgSet = [RO.Wdg.IntLabel(self,
                width = 4,
                helpText = "current overscan in %s (binned pix)" % ccdDescr[ii],
                helpURL = self.HelpPrefix + "Overscan",
            )
            for ii in range(2)
        ]
        self.model.ccdOverscan.addROWdgSet(ccdOverscanCurrWdgSet)

        self.ccdOverscanUserWdgSet = [
            RO.Wdg.IntEntry(self,
                minValue = 0,
                maxValue = 2048,
                width = 4,
                helpText = "requested overscan in %s (binned pix)" % ccdDescr[ii],
                helpURL = self.HelpPrefix + "Overscan",
                clearMenu = None,
                defMenu = "Current",
                autoIsCurrent = True,
            )
            for ii in range(2)
        ]
        self.model.ccdOverscan.addROWdgSet(self.ccdOverscanUserWdgSet, setDefault=True)
        gr.gridWdg (
            label = "Overscan",
            dataWdg = ccdOverscanCurrWdgSet,
            units = "bpix",
            cfgWdg = self.ccdOverscanUserWdgSet,
            cat = self.CCDCat,
        )

        # set up format functions for the various pop-up menus
        # these allow us to return index values instead of names
        class indFormat(object):
            def __init__(self, indFunc, offset=1):
                self.indFunc = indFunc
                self.offset = offset
            def __call__(self, inputCont):
                valueList = inputCont.getValueList()
                if not valueList:
                    return ''
                name = inputCont.getName()
                return "%s=%d" % (name, self.indFunc(valueList[0]) + self.offset)
        
        # At this point the widgets are all set up;
        # set the flag (so showHideWdg works)
        self.gridder.allGridded()       

        # add callbacks that access widgets
        self.model.maskNames.addCallback(self.maskNameUserWdg.setItems)
        self.model.maskName.addIndexedCallback(self.maskNameUserWdg.setDefault, 0)
        self.model.filterNames.addCallback(self.filterNameUserWdg.setItems)
        self.model.filterName.addIndexedCallback(self.filterNameUserWdg.setDefault, 0)
        self.model.turretName.addIndexedCallback(self._doTurretName, 0)
        self.model.turretName.addIndexedCallback(self.turretNameUserWdg.setDefault, 0)
        self.model.ccdUBWindow.addCallback(self._setCCDWindowWdgDef)
        self.model.ccdWindow.addCallback(self._updCurrImageSize)

        # set up correct show/hide state        
        self._showHideGratingWdg()

        # set up the input container set; this is what formats the commands
        # and allows saving and recalling commands
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = "motor mask",
                    wdgs = self.maskNameUserWdg,
                    formatFunc = indFormat(self.maskNameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "motors filter",
                    wdgs = self.filterNameUserWdg,
                    formatFunc = indFormat(self.filterNameUserWdg.index),
                ),
                RO.InputCont.WdgCont (
                    name = "motors turret",
                    wdgs = self.turretNameUserWdg,
                    formatFunc = indFormat(getTurretIndex, offset=0),
                ),
                RO.InputCont.WdgCont (
                    name = "motors b1lambda",
                    wdgs = self.lambdaUserWdgSet[1][0],
                    formatFunc = RO.InputCont.BasicFmt(nameSep = '='),
                ),
                RO.InputCont.WdgCont (
                    name = "motors r1lambda",
                    wdgs = self.lambdaUserWdgSet[1][1],
                    formatFunc = RO.InputCont.BasicFmt(nameSep = '='),
                ),
                RO.InputCont.WdgCont (
                    name = "motors b2lambda",
                    wdgs = self.lambdaUserWdgSet[2][0],
                    formatFunc = RO.InputCont.BasicFmt(nameSep = '='),
                ),
                RO.InputCont.WdgCont (
                    name = "motors r2lambda",
                    wdgs = self.lambdaUserWdgSet[2][1],
                    formatFunc = RO.InputCont.BasicFmt(nameSep = '='),
                ),
                RO.InputCont.WdgCont (
                    name = "bin",
                    wdgs = self.ccdBinUserWdgSet,
                    formatFunc = RO.InputCont.BasicFmt(
                        rejectBlanks = True,
                    ),
                ),
                RO.InputCont.WdgCont (
                    name = "window",
                    wdgs = self.ccdWindowUserWdgSet,
                    formatFunc = RO.InputCont.BasicFmt(
                        rejectBlanks = True,
                    ),
                ),
                RO.InputCont.WdgCont (
                    name = "overscan",
                    wdgs = self.ccdOverscanUserWdgSet,
                    formatFunc = RO.InputCont.BasicFmt(
                        rejectBlanks = True,
                    ),
                ),
            ],
        )
        
        def repaint(evt):
            self.restoreDefault()
        self.bind("<Map>", repaint)
    
    def getTurretIndex(self):
        turretName = self.turretNameUserWdg.getString()
        return self.turretIndexDict.get(turretName)

    def getGratingSetID(self):
        """Returns the current grating set ID, or None if none"""
        turretIndex = self.getTurretIndex()
        if turretIndex in (1, 2):
            return turretIndex
        return None

    def _doTurretName(self, turretName, isCurrent, **kargs):
        if turretName != None and turretName.startswith("change"):
            severity = RO.Constants.sevWarning
        else:
            severity = RO.Constants.sevNormal
        self.turretNameCurrWdg.set(
            turretName,
            isCurrent = isCurrent,
            severity = severity,
        )
    
    def _saveCCDUBWindow(self):
        """Save user ccd window in unbinned pixels.
        """
        if self._freezeCCDUBWindow:
            return

        userWindow = [wdg.getNum() for wdg in self.ccdWindowUserWdgSet]
        if 0 in userWindow:
            return
        userBinFac = self._getUserBinFac()
        if 0 in userBinFac:
            return
        self.userCCDUBWindow = self.model.unbin(userWindow, userBinFac) 
    
    def _setCCDWindowWdgDef(self, *args, **kargs):
        """Updates the default value of CCD window wdg.
        If this has the effect of changing the displayed values
        (only true if a box is blank) then update the saved unbinned window.
        """
        if self.userCCDUBWindow == None:
            currUBWindow, isCurrent = self.model.ccdUBWindow.get()
            if isCurrent:
                self.userCCDUBWindow = currUBWindow

        initialUserCCDWindow = self._getUserCCDWindow()
#       print "_setCCDWindowWdgDef; initialUserCCDWindow =", initialUserCCDWindow
        self._updUserCCDWindow(doCurrValue=False)
        if initialUserCCDWindow != self._getUserCCDWindow():
#           print "_setCCDWindowWdgDef; user value changed when default changed; save new unbinned value"
            self._saveCCDUBWindow()

    def _userBinChanged(self, *args, **kargs):
        """User bin factor changed.
        Update ccd window current values and default values.
        """
        self._updUserCCDWindow()
    
    def _userWindowChanged(self, *args, **kargs):
        self._saveCCDUBWindow()
            
        # update user ccd image size
        actUserCCDWindow = self._getUserCCDWindow()
        if 0 in actUserCCDWindow:
            return
        for ind in range(2):
            imSize = 1 + actUserCCDWindow[ind+2] - actUserCCDWindow[ind]
            self.ccdImageSizeUserWdgSet[ind].set(imSize)
        

    def _updCurrImageSize(self, *args, **kargs):
        """Updates current image size.
        """
        window, isCurrent = self.model.ccdWindow.get()
        if not isCurrent:
            return

        try:
            imageSize = [1 + window[ind+2] - window[ind] for ind in range(2)]
        except TypeError:
            imageSize = (None, None)

        for ind in range(2):
            self.ccdImageSizeCurrWdgSet[ind].set(imageSize[ind])
    
    def _updUserCCDWindow(self, doCurrValue = True):
        """Update user-set ccd window.
        
        Inputs:
        - doCurrValue: if True, set current value and default;
            otherwise just set default.
        
        The current value is set from the cached user's unbinned value
        """
        self._freezeCCDUBWindow = True
        try:
            if doCurrValue and self.userCCDUBWindow == None:
#               print "_updUserCCDWindow; unbinned = none"
                return
            userBinFac = self._getUserBinFac()
#           print "_updUserCCDWindow; userBinFac =", userBinFac
            if 0 in userBinFac:
#               print "_updUserCCDWindow; bin fac has 0"
                return
            
            # update user ccd window displayed value, default valud and limits
            if doCurrValue:
                userWindow = self.model.bin(self.userCCDUBWindow, userBinFac)
            currUBWindow, isCurrent = self.model.ccdUBWindow.get()
            if isCurrent:
                currWindow = self.model.bin(currUBWindow, userBinFac)
            else:
                currWindow = (None,)*4
#           print "_updUserCCDWindow; currWindow=", currWindow
            minWindowXYXY = self.model.minCoord(userBinFac)*2
            maxWindowXYXY = self.model.maxCoord(userBinFac)*2
#           print "_updUserCCDWindow: setting values", userWindow
            for ind in range(4):
                wdg = self.ccdWindowUserWdgSet[ind]
                
                # disable limits
                wdg.setRange(
                    minValue = None,
                    maxValue = None,
                )
                
                # set displayed and default value
                if doCurrValue:
                    wdg.set(userWindow[ind], isCurrent)
                wdg.setDefault(currWindow[ind], isCurrent)
                
                # set correct range for this bin factor
                wdg.setRange(
                    minValue = minWindowXYXY[ind],
                    maxValue = maxWindowXYXY[ind],
                )

        finally:
            self._freezeCCDUBWindow = False
        
    def _getUserBinFac(self):
        """Return the current user-set bin factor in x and y.
        """
        return [wdg.getNum() for wdg in self.ccdBinUserWdgSet]
    
    def _getUserCCDWindow(self):
        """Return the current user-set ccd window (binned) in x and y.
        """
        return [wdg.getNum() for wdg in self.ccdWindowUserWdgSet]
    
    def _showHideGratingWdg(self, *args):
        """Turret position changed;
        show or hide grating setting widgets accordingly.
        """
        gsid = self.getGratingSetID()

        argDict = {
            self.GSCat[1]: gsid == 1,
            self.GSCat[2]: gsid == 2,
        }
        self.gridder.showHideWdg (**argDict)


if __name__ == "__main__":
    root = RO.Wdg.PythonTk()

    import TestData
        
    testFrame = StatusConfigInputWdg (root)
    testFrame.pack()
    
    TestData.dispatch()
    
    testFrame.restoreDefault()

    def printCmds():
        cmdList = testFrame.getStringList()
        for cmd in cmdList:
            print cmd
    
    bf = Tkinter.Frame(root)
    cfgWdg = RO.Wdg.Checkbutton(bf, text="Config", defValue=True)
    cfgWdg.pack(side="left")
    Tkinter.Button(bf, text="Cmds", command=printCmds).pack(side="left")
    Tkinter.Button(bf, text="Current", command=testFrame.restoreDefault).pack(side="left")
    Tkinter.Button(bf, text="Demo", command=TestData.animate).pack(side="left")
    bf.pack()

    testFrame.gridder.addShowHideControl(testFrame.ConfigCat, cfgWdg)

    root.mainloop()
