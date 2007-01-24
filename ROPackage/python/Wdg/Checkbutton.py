#!/usr/bin/env python
"""A variant on Checkbutton that add help, default handling and other niceties
including a command callback that is called in more cases.

Warning: if indicatoron is false then selectcolor is forced
to the background color (since selectcolor is used for
the text background, which is also affected by isCurrent).

To do:
- examine defaults for MacOS X. There appears to be a really big border
around the widget that is unnecessary and means there is not enough room
for text. At least make the default y padding bigger on MacOS X
when indicatoron false -- right now the border is much too close to the text!

History:
2002-11-15 ROwen
2002-12-04 ROwen    Added support for helpURL.
2003-03-13 ROwen    Renamed from ROCheckbutton to Checkbutton;
                    added defIfDisabled, setEnable and class EnableCheckbutton.
2003-04-15 ROwen    Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-05-29 ROwen    Removed EnableCheckbutton (it's obsolete).
2003-07-09 ROwen    Added addCallback, clear, getEnable and setBool;
                    modified to use RO.AddCallback.
2003-08-04 ROwen    Improved callbacks to fire when command fires (a bit later in the process;
                    prevents display bugs in some applications).
2003-08-11 ROwen    Added set, asBool; changed isSelected to getBool.
2003-11-03 ROwen    Modified so callbacks are called for set, setBool, select, etc.
                    or when the variable is set. These are all cases in which
                    standard Tk Checkbutton command callbacks are NOT called.
2003-12-02 ROwen    Bug fix: getBool would always return False if a BooleanVar was used.
                    Modified asBool to return False in the case of a string that does not match onvalue,
                    instead of raising an exception if the string didn't match onvalue or offvalue.
                    Added some doc strings.
2003-12-05 ROwen    Changed setDefValue to setDefault for consistency.
2003-12-19 ROwen    Added showValue arg to __init__.
                    Improved documentation and checking of **kargs for __init__.
                    Added *args, **kargs to set and setDefault
                    so they can be called by KeyVariable addROWdg.
2004-05-18 ROwen    Modified so indicatoron tested for logical false when tweaking
                    selectcolor. This still doesn't handle "f" and other tk-ish
                    logical values, but is clearer for python-ish logical values
                    and makes pychecker happier.
2004-08-11 ROwen    Define __all__ to restrict import.
2004-09-14 ROwen    Tweaked the imports.
2004-11-15 ROwen    Improved defaults: if showValue True then defaults to indicatoron = False;
                    if indicatoron = False then defaults to padx=5, pady=2.
2004-12-27 ROwen    Corrected documentation for set and setDefault.
2005-01-05 ROwen    Added autoIsCurrent, isCurrent and severity support.
2005-05-10 ROwen    Bug fix: setBool ignored isCurrent and severity.
2005-06-02 ROwen    Modified default padding when indicatoron is false
                    so it looks better under Tk 8.4.9, especially on Aqua
                    (something changed in Tk at some point such that
                    the old aqua margins were too small).
2005-07-07 ROwen    Modified for moved TkUtil.
2005-09-15 ROwen    If var supplied and defValue left None
                    then the default value is the current value of var.
2007-01-11 ROwen    Added isDefault method.
"""
__all__ = ['Checkbutton']

import Tkinter
import RO.AddCallback
import RO.CnvUtil
import RO.MathUtil
import RO.TkUtil
from CtxMenu import CtxMenuMixin
from IsCurrentMixin import AutoIsCurrentMixin, IsCurrentCheckbuttonMixin
from SeverityMixin import SeverityActiveMixin

class Checkbutton (Tkinter.Checkbutton, RO.AddCallback.TkVarMixin,
    AutoIsCurrentMixin, IsCurrentCheckbuttonMixin, SeverityActiveMixin, CtxMenuMixin):
    """A Checkbutton with callback, help, isCurrent and severity support.
    
    Inputs:
    - var       a Tkinter variable; this is updated when Checkbutton state changes
                (and also during initialization if defValue != None)
    - defValue  the default state: either a string (which must match on or off value)
                or a bool (selected if True, unselected if False)
                or None (default), meaning use var if supplied, else False.
    - helpText  text for hot help
    - helpURL   URL for longer help
    - callFunc  callback function; the function receives one argument: self.
                It is called whenever the value changes (manually or via
                the associated variable being set) and when setDefault is called
                (unlike command, which is only called for user action and invoke()).
    - defIfDisabled show the default value if disabled (via doEnable)?
    - showValue Display text = current value;
                overrides text and textvariable
    - autoIsCurrent controls automatic isCurrent mode
        - if false (manual mode), then is/isn't current if set, setBool
            or setIsCurrent is called with isCurrent true/false
        - if true (auto mode), then is currently only when all these are so:
            - set, setBool or setIsCurrent is called with isCurrent true
            - setDefValue is called with isCurrent true
            - current value == default value
    - isCurrent: is the default value (used as the initial value) current?
    - severity  initial severity; one of RO.Constants.sevNormal, sevWarning or sevError
    - all remaining keyword arguments are used to configure the Tkinter Checkbutton;
      - command is supported, but see also the callFunc argument
      - variable is forbidden (use var)
      - text and textvariable are forbidden if showValue is true
      - selectcolor is ignored and forced equal to background if indicatoron false
        (i.e. if no checkbox is shown)

    Inherited methods include:
    addCallback, removeCallback
    getIsCurrent, setIsCurrent
    getSeverity, setSeverity
    """
    def __init__(self,
        master,
        var = None,
        defValue = None,
        helpText = None,
        helpURL = None,
        callFunc = None,
        defIfDisabled = False,
        showValue = False,
        autoIsCurrent = False,
        isCurrent = True,
        severity = RO.Constants.sevNormal,
    **kargs):
        self._defBool = False # just create the field for now
        if var == None:
            var = Tkinter.StringVar()
        elif defValue == None:
            defValue = var.get()
        self._var = var
        self._defIfDisabled = bool(defIfDisabled)
        self.helpText = helpText
        
        # if a command is supplied in kargs, remove it now and set it later
        # so it is not called during init
        cmd = kargs.pop("command", None)
        if "variable" in kargs:
            raise ValueError("Specify var instead of variable")
        if showValue:
            if "text" in kargs:
                raise ValueError("Do not specify text if showValue True")
            if "textvariable" in kargs:
                raise ValueError("Do not specify textvariable if showValue True (specify var instead)")
            kargs.setdefault("indicatoron", False)
            kargs["textvariable"] = self._var
        
        if not RO.CnvUtil.asBool(kargs.get("indicatoron", True)):
            # user wants text, not a checkbox;
            # on Aqua adjust default padding so text can be read
            if RO.TkUtil.getWindowingSystem() == RO.TkUtil.WSysAqua:
                kargs.setdefault("padx", 6)
                kargs.setdefault("pady", 5)
            else:
                kargs.setdefault("padx", 2)

        Tkinter.Checkbutton.__init__(self,
            master = master,
            variable = self._var,
        **kargs)

        RO.AddCallback.TkVarMixin.__init__(self, self._var)
        
        CtxMenuMixin.__init__(self,
            helpURL = helpURL,
        )

        AutoIsCurrentMixin.__init__(self, autoIsCurrent)
        IsCurrentCheckbuttonMixin.__init__(self)
        SeverityActiveMixin.__init__(self, severity)

        self._defBool = self.asBool(defValue)
        self._isCurrent = isCurrent
        if self._defBool:
            self.select()
        else:
            self.deselect()
        
        # add the callbacks last, so the autoIsCurrent callback
        # is called first and to avoid calling them while setting default
        self.addCallback(callFunc, False)
        if cmd:
            self["command"] = cmd
        
    def asBool(self, val):
        """Returns a value as a bool.
        
        The input value can be any of:
        - a string: returns True if matches onvalue (case sensitive), else False*
        - True, False: returns val
        - anything else: returns bool(val)
        
        *This matches the behavior of checkbuttons (based on observation on one platform,
        so this may not always be true): they are checked if the value matches onvalue,
        else unchecked.
        """
        if hasattr(val, "lower"):
            if val == self["onvalue"]:
                return True
            else:
                return False

        return bool(val)
    
    def clear(self):
        """Convenience function, makes it work more like an RO.Wdg.Entry widget.
        """
        self.deselect()
    
    def getBool(self):
        """Returns True if the checkbox is selected (checked), False otherwise.
        """
        return self.asBool(self._var.get())
    
    def getDefBool(self):
        """Returns True if the checkbox is selected (checked) by default, False otherwise.
        """
        return self._defBool

    def getDefault(self):
        """Returns onvalue if the default is selected (checked) by default, offvalue otherwise.
        Onvalue and offvalue are strings.
        """
        if self._defBool:
            return self["onvalue"]
        else:
            return self["offvalue"]

    def getEnable(self):
        """Returns True if the button is enabled, False otherwise.
        
        Enabled is defined as the state not being 'disabled'.
        """
        return self["state"] != "disabled"
    
    def getVar(self):
        return self._var
    
    def getString(self):
        return str(self._var.get())
    
    def isDefault(self):
        """Return True if current value matches default"""
        return self.getBool() == self.getDefBool()
    
    def restoreDefault(self):
        """Restores the default value. Calls callbacks (if any).
        """
        if self._defBool:
            self.select()
        else:
            self.deselect()

    def set(self,
        newValue,
        isCurrent = True,
        severity = None,
    **kargs):
        """Set value (checking or unchecking the box) and trigger the callback functions.
        
        Inputs:
        - value: the new value.
            - If a string, then the box is checked if value matches
            self["onvalue"] (case matters) and unchecked otherwise.
            - If not a string then the value is coerced to a bool
            and the box is checked if true, unchecked if false.
        - isCurrent: is value current? (if not, display with bad background color)
        - severity: the new severity, one of: RO.Constants.sevNormal, sevWarning or sevError;
          if omitted, the severity is left unchanged          
        kargs is ignored; it is only present for compatibility with KeyVariable callbacks.
        """
        self.setBool(self.asBool(newValue), isCurrent=isCurrent, severity=severity)
    
    def setBool(self,
        boolState,
        isCurrent = True,
        severity = None,
    ):
        """Checks or unchecks the checkbox.
        
        Inputs:
        - boolState: new boolean state; check/uncheck box if true/false
        - isCurrent: is value current (if not, display with bad background color)
        - severity: the new severity, one of: RO.Constants.sevNormal, sevWarning or sevError;
          if omitted, the severity is left unchanged          
        """
        if boolState:
            self.select()
        else:
            self.deselect()
        self.setIsCurrent(isCurrent)
        if severity != None:
            self.setSeverity(severity)

    def setDefault(self,
        newDefValue,
        isCurrent = None,
    **kargs):
        """Changes the default value, triggers the callback functions
        and (if widget disabled and defIfDisabled true) updates the displayed value.
        
        Inputs:
        - value: the new default value.
            - If a string, then the default is checked if value matches
            self["onvalue"] (case matters) and unchecked otherwise.
            - If not a string then the value is coerced to a bool
            and the default is checked if true, unchecked if false.
        - isCurrent: if not None, set the _isCurrent flag accordingly.
            Typically this is only useful in autoIsCurrent mode.
        kargs is ignored; it is only present for compatibility with KeyVariable callbacks.
        """
        self._defBool = self.asBool(newDefValue)
        if isCurrent != None:
            self._isCurrent = isCurrent
        
        # if disabled and defIfDisabled, update display
        # (which also triggers a callback)
        # otherwise leave the display alone and explicitly trigger a callback
        if self._defIfDisabled and self["state"] == "disabled":
            self.restoreDefault()
        else:
            self._doCallbacks()

    def setEnable(self, doEnable):
        """Changes the enable state and (if the widget is being disabled
        and defIfDisabled true) displays the default value
        """
        if doEnable:
            self.configure(state="normal")
        else:
            self.configure(state="disabled")
            if self._defIfDisabled:
                self.restoreDefault()


if __name__ == "__main__":
    import PythonTk
    root = PythonTk.PythonTk()
    
    def btnCallback(btn):
        print "%s state=%s" % (btn["text"], btn.getBool())

    Checkbutton(root,
        text = "Auto Bgnd",
        defValue = False,
        callFunc = btnCallback,
        helpText = "Help for checkbox 'Auto Bgnd', default off",
        autoIsCurrent = True,
    ).pack()
    Checkbutton(root,
        text = "Manual",
        defValue = True,
        callFunc = btnCallback,
        helpText = "Help for checkbox 'Manual', default on",
    ).pack()
    var = Tkinter.StringVar()
    Checkbutton(root,
        text = "Auto Bgnd 2",
        defValue = True,
        callFunc = btnCallback,
        helpText = "Help for checkbox 'Auto Bgnd 2', default on",
        indicatoron = False,
        autoIsCurrent = True,
    ).pack()
    Checkbutton(root,
        text = "Manual 2",
        defValue = True,
        callFunc = btnCallback,
        helpText = "Help for checkbox 'Manual 2', default on",
        indicatoron = False,
    ).pack()

    root.mainloop()
