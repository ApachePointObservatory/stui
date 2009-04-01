#!/usr/bin/env python
"""Allows the user to specify rotation type and rotation angle.

History:
2001-11-05 ROwen    First version with history.
2002-06-11 ROwen    Disables invalid rot types based on coordSysvar.
2002-06-25 ROwen    Removed an unneeded keyword from inputCont.
2002-07-31 ROwen    Modified to use the RO.CoordSys module.
2002-08-02 ROwen    Changed the default angle to from 0 to "0"
                    (no decimal pt shown)
2002-08-02 ROwen    Mod. rot. type menu to take focus and have a separator.
2002-11-15 ROwen    Mod. to use ROOptionMenu and added help strings.
2002-11-26 ROwen    Changed to URL-based help.
2003-03-11 ROwen    Changed to use OptionMenu instead of ROOptionMenu.
2003-03-21 ROwen    Fixed accessing of menu from rotTypeWdg.
2003-03-26 ROwen    Use the tcc model to disable wdg if no rot;
                    this means RotWdg now needs the dispatcher.
2003-04-14 ROwen    Modified to use TUI.TCC.UserModel.
2003-04-28 ROwen    Added rotType to user model;
                    added update of rotator limits for mount rotation;
                    added disable of rot angle if rot type is None.
2003-06-09 ROwen    Removed dispatcher arg.
2003-06-13 ROwen    Implemented helpText.
2003-07-10 ROwen    Modified to use overhauled RO.InputCont.
2003-10-23 ROwen    Modified to allow abbreviations.
2003-10-24 ROwen    Added userModel input.
2005-08-01 ROwen    Corrected an indentation inconsistency.
2008-04-28 ROwen    Strip "+" symbols from values since the TCC can't handle them.
2009-04-01 ROwen    Updated test code to use TUI.Base.TestDispatcher.
"""
import Tkinter
import RO.CoordSys
import RO.InputCont
import RO.Wdg
import RO.StringUtil
import TUI.TCC.TCCModel
import TUI.TCC.UserModel

_rt_Object = "Object"
_rt_Horizon = "Horizon"
_rt_Mount = "Mount"
_rt_None = "None"

_RotTypeMenuItems = (
    _rt_Object,
    _rt_Horizon,
    None,
    _rt_Mount,
    _rt_None,
)

_RotTypeHelpDict = {
    _rt_Object: "Rotate with object",
    _rt_Horizon: "Rotate with horizon",
    _rt_Mount: "Move rotator to a fixed angle",
    _rt_None: "Leave the rotator where it is",
}

_RotAngHelpDict = {
    _rt_Object: "Angle of object with respect to the instrument",
    _rt_Horizon: "Angle of az/alt with respect to the instrument",
    _rt_Mount: "Angle sent to the rotator controller",
}

_HelpPrefix = "Telescope/SlewWin/index.html#"

_StdRotLim = [-360, 360]

class RotWdg (RO.Wdg.InputContFrame):
    """Allows the user to specify rotation type and rotation angle.

    Inputs:
    - master        master Tk widget -- typically a frame or window
    - userModel     a TUI.TCC.UserModel; specify only if global model
                    not wanted (e.g. for checking catalog values);
                    if specified, assumes rot exists with std limits
    - **kargs       keyword arguments for Tkinter.Frame
    """
    # rotation types

    def __init__ (self,
        master,
        userModel = None,
    **kargs):
        RO.Wdg.InputContFrame.__init__(self, master, **kargs)
        self.coordSys = None
        self.rotLim = _StdRotLim
        self.rotExists = True

        self.userModel = userModel or TUI.TCC.UserModel.Model()
            
                
        self.rotAngWdg = RO.Wdg.FloatEntry(self,
            minValue = self.rotLim[0],
            maxValue = self.rotLim[1],
            defValue = "0",
            defFormat = "%.2f",
            helpURL = _HelpPrefix + "RotAngle",
            minMenu = "Minimum",
            maxMenu = "Maximum",
        )
        self.rotAngWdg.grid(row=0, column=0)
        
        Tkinter.Label(self, text=RO.StringUtil.DegStr).grid(row=0, column=1)

        self.rotTypeWdg = RO.Wdg.OptionMenu(self,
            items = _RotTypeMenuItems,
            defValue = _rt_Object,
            abbrevOK = True,
            ignoreCase = True,
            var = self.userModel.rotType.getVar(),
            helpText = [_RotTypeHelpDict.get(item) for item in _RotTypeMenuItems],
            helpURL = "Telescope/RotTypes.html",
        )
        self.rotTypeWdg.grid(row=0, column=2)

        if not userModel:
            # uses global user model,
            # hence wants normal connection to rot info
            tccModel = TUI.TCC.TCCModel.Model()
            tccModel.ipConfig.addCallback(self._ipConfigCallback, callNow=False)
            tccModel.rotLim.addCallback(self._rotLimCallback)
        self.userModel.coordSysName.addCallback(self._coordSysChanged)
        self.userModel.rotType.addCallback(self._rotTypeChanged)

        # create a set of input widget containers
        # for easy set/get of data
        self.inputCont = RO.InputCont.ContList (
            conts = [
                RO.InputCont.WdgCont (
                    name = "RotAngle",
                    wdgs = self.rotAngWdg,
                    omitDef = False,
                    formatFunc = RO.InputCont.VMSQualFmt(stripPlusses=True),
                ),
                RO.InputCont.WdgCont (
                    name = "RotType",
                    wdgs = self.rotTypeWdg,
                    omitDef = False,
                    formatFunc = RO.InputCont.VMSQualFmt(),
                ),
            ],
            formatFunc = RO.InputCont.BasicContListFmt(valSep = ""),
        )
    
    def _ipConfigCallback(self, keyVar):
        #print "%s._ipConfigCallback(%s)" % (self.__class__.__name__, keyVar)
        if not keyVar.isCurrent:
            return
        ipConfig = keyVar[0]
        self.rotExists = ipConfig.lower()[0] == "t"
        self._setEnable()
    
    def _rotLimCallback(self, keyVar):
        rotLim = keyVar.valueList
        if None in rotLim:
            return
        self.rotLim = rotLim[0:2]
        self._rotTypeChanged(self.userModel.rotType.get())
    
    def _rotTypeChanged(self, rotType):
        if rotType == "Mount":
            self.rotAngWdg.setRange(*self.rotLim)
        else:
            self.rotAngWdg.setRange(*_StdRotLim)
        self._setEnable()
        self.rotAngWdg.helpText = _RotAngHelpDict.get(rotType)
    
    def _setEnable(self):
        rotType = self.userModel.rotType.get()
        self.rotTypeWdg.setEnable(self.rotExists)
        self.rotAngWdg.setEnable(self.rotExists and (rotType != "None"))

    def _coordSysChanged (self, coordSys):
        if coordSys == self.coordSys:
            return
    
        rotType = self.userModel.rotType.get()
        rotTypeMenu = self.rotTypeWdg.getMenu()
        physMountCSysSet = (RO.CoordSys.Physical, RO.CoordSys.Mount)
        if coordSys in physMountCSysSet:
            if self.coordSys not in physMountCSysSet:
                # changed from all acceptable or unknown to some acceptable
                # only phys, mount and none are acceptable; disable the others
                # and try to set a default of mount, no value, value required
                rotTypeMenu.entryconfigure(0, state="disabled")
                rotTypeMenu.entryconfigure(1, state="disabled")
                if rotType in (_rt_Object, _rt_Horizon):
                    self.userModel.rotType.set(_rt_None)
        else:
            if self.coordSys in physMountCSysSet:
                # changed from some acceptable or unknown to all acceptable
                # all are acceptable; default is 0 deg Obj
                rotTypeMenu.entryconfigure(0, state="normal")
                rotTypeMenu.entryconfigure(1, state="normal")
                if rotType != _rt_None:
                    self.userModel.rotType.set(_rt_Object)
        self.coordSys = coordSys

if __name__ == "__main__":
    import Tkinter
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot
    
    def restoreDefault():
        rotWdg.restoreDefault()
        
    def printOptions(*args):
        print rotWdg.getString()
        
    getButton = Tkinter.Button (root, command=restoreDefault, text="Defaults")
    getButton.pack()
        
    getButton = Tkinter.Button (root, command=printOptions, text="Print Options")
    getButton.pack()
    
    rotWdg = RotWdg(root)
    rotWdg.pack()

    tuiModel.reactor.run()
