#!/usr/local/bin/python
"""RO.Wdg.Label widgets are display widgets that store data in its most basic form,
yet know how to format it for display. These widgets consider their data to be bad
(and display it with a bad background color) if the value is None or the value is not current.

Background color is handled as follows:
- Good (normal) background color is copied from a widget whose background is never directly
  modified; hence it tracks changes to the global application background color
- Bad background color cannot be handled in this fashion, so a preference variable is used
  and a callback is registered (that's going to be a painfully slow callback if there
  are a lot of widgets to update).

History:
2002-01-25 ROwen    Fixed handling of default background color;
                    now it is read from the widget when that widget is first created,
                    so all the standard techniques work for setting that color.
2002-01-30 ROwen    Improved background color handling again;
                    it is always read from the option database when the state changes.
2002-03-14 ROwen    Modified to handle isValid argument;
                    modified get to return isValid in the tuple; fixed get to return a value instead of None.
2002-03-18 ROwen    Repackaged as part of larger RO.Wdg package.
2002-11-15 ROwen    Added use of CtxMenuMixin.
2002-11-26 ROwen    Added support for helpURL.
2002-12-04 ROwen    Swapped helpURL and helpText args.
2002-12-20 ROwen    Bug fixes: _subscribeStatePrefs was specifying a callback to a nonexistent function;
                    setNotCurrent called setIsCurrent with an extraneous "self";
                    corrected typo in error message (pint for point); thanks to pychecker.
2003-03-05 ROwen    Removed all isValid handling; invalid values have value None
2003-03-06 ROwen    Fixed default precision for FloatLabel (was None, which caused errors).
2003-03-17 ROwen    Fixed StrLabels to handle unicode.
2003-04-15 ROwen    Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-06-17 ROwen    Modified to be in current state by default (so can be used as a general label);
                    overhauled setting of state and improved lazy subscription to state colors.
2003-06-18 ROwen    Modified to pass SystemExit and KeyboardInterrupt when
                    testing for general errors.
2003-07-25 ROwen    Modified to allow a format string.
2003-12-19 ROwen    Added BoolLabel. Added tests for disallowed keywords.
2004-08-11 ROwen    Modified to use Constants and WdgPrefs.
                    Use modified state constants with sev prefix.
                    Define __all__ to restrict import.
2004-09-03 ROwen    Modified for RO.Wdg.sev... -> RO.Constants.sev...
2004-09-14 ROwen    Bug fix: isCurrent was ignored for most classes.
2004-11-16 ROwen    Changed _setState method to setState.
2004-12-29 ROwen    Modified to use IsCurrentMixin and SeverityMixin.
                    Modified to allow setting initial state.
                    Changed _setIsCurrent method to setIsCurrent.
2005-01-05 ROwen    Changed message state to severity, set/getState to set/getSeverity.
"""
__all__ = ['Label', 'BoolLabel', 'StrLabel', 'IntLabel', 'FloatLabel', 'DMSLabel']

import sys
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.StringUtil
import CtxMenu
import WdgPrefs
from SeverityMixin import SeverityMixin
from IsCurrentMixin import IsCurrentMixin

class Label(Tkinter.Label, CtxMenu.CtxMenuMixin, IsCurrentMixin, SeverityMixin):
    """Base class for labels (display ROWdgs); do not use directly.
    
    Inputs:
    - formatStr: formatting string; if omitted, formatFunc is used.
        Displayed value is formatStr % value.
    - formatFunc: formatting function; ignored if formatStr specified.
        Displayed value is formatFunc(value).
    - helpText  short text for hot help
    - helpURL   URL for on-line help
    - isCurrent is value current?
    - severity  one of RO.Constants.sevNormal, sevWarning or sevError
    - **kargs: all other keyword arguments go to Tkinter.Label;
        the defaults are anchor="e", justify="r"
        
    Inherited methods include:
    getIsCurrent, setIsCurrent
    getSeverity, setSeverity
        
    Note: if display formatting fails (raises an exception)
    then "?%r?" % value is displayed.
    """

    def __init__ (self,
        master,
        formatStr = None,
        formatFunc = unicode,       
        helpText = None,
        helpURL = None,
        isCurrent = True,
        severity = RO.Constants.sevNormal,
    **kargs):
        kargs.setdefault("anchor", "e")
        kargs.setdefault("justify", "r")
        
        Tkinter.Label.__init__(self, master, **kargs)
        
        CtxMenu.CtxMenuMixin.__init__(self, helpURL=helpURL)
        
        IsCurrentMixin.__init__(self, isCurrent)
        
        SeverityMixin.__init__(self, severity)

        self._formatStr = formatStr
        if formatStr != None:
            formatFunc = self._formatFromStr
        self._formatFunc = formatFunc
        self.helpText = helpText

        self._value = None

    def get(self):
        """Return a tuple consisting of (set value, isCurrent).
        
        If the value is None then it is invalid or unknown.
        If isCurrent is false then the value is suspect
        Otherwise the value is valid and current.
        """
        return (self._value, self._isCurrent)
    
    def getFormatted(self):
        """Return a tuple consisting of the (displayed value, isCurrent).
        
        If the value is None then it is invalid.
        If isCurrent is false then the value is suspect
        Otherwise the value is valid and current.
        """
        if self._value == None:
            return (None, self._isCurrent)
        else:
            return (self["text"], self._isCurrent)
    
    def clear(self, isCurrent=1):
        """Clear the display; leave severity unchanged.
        """
        self.set(value="", isCurrent=isCurrent)
    
    def set(self,
        value,
        isCurrent = True,
        severity = None,
    **kargs):
        """Set the value

        Inputs:
        - value: the new value
        - isCurrent: is value current (if not, display with bad background color)
        - severity: the new severity, one of: RO.Constants.sevNormal, sevWarning or sevError;
          if omitted, the severity is left unchanged          
        kargs is ignored; it is only present for compatibility with KeyVariable callbacks.
        
        Raises an exception if the value cannot be coerced.
        """
        # print "RO.Wdg.Label.set called: value=%r, isCurrent=%r, **kargs=%r" % (value, isCurrent, kargs)
        self._value = value
        self.setIsCurrent(isCurrent)
        if severity != None:
            self.setSeverity(severity)
        self._updateText()
    
    def setNotCurrent(self):
        """Mark the data as not current.
        
        To mark the value as current again, set a new value.
        """
        self.setIsCurrent(False)
    
    def _formatFromStr(self, value):
        """Format function based on formatStr.
        """
        return self._formatStr % value

    def _updateText(self):
        """Updates the displayed value. Ignores isCurrent and severity.
        """
        if self._value == None:
            self["text"] = ""
        else:
            try:
                self["text"] = self._formatFunc(self._value)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                sys.stderr.write("format of value %r failed with error: %s\n" % (self._value, e))
                self["text"] = "?%r?" % (self._value,)


class BoolLabel(Label):
    """Label to display string data.
    Inputs are those for Label, but formatStr and formatFunc are forbidden.
    """
    def __init__ (self,
        master,
        helpText = None,
        helpURL = None,
        trueValue = "True",
        falseValue = "False",
        isCurrent = True,
        **kargs
    ):
        assert not kargs.has_key("formatStr"), "formatStr not allowed for %s" % self.__class__.__name__
        assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__

        def formatFnct(val):
            if val:
                return trueValue
            else:
                return falseValue

        Label.__init__(self,
            master,
            formatFunc = formatFnct,
            helpText = helpText,
            helpURL = helpURL,
            isCurrent = isCurrent,
        **kargs)


class StrLabel(Label):
    """Label to display string data.
    Inputs are those for Label but the default formatFunc is str.
    """
    def __init__ (self,
        master,
        helpText = None,
        helpURL = None,
        isCurrent = True,
        **kargs
    ):
        kargs.setdefault("formatFunc", str)
        
        Label.__init__(self,
            master,
            helpText = helpText,
            helpURL = helpURL,
            isCurrent = isCurrent,
        **kargs)


class IntLabel(Label):
    """Label to display integer data; truncates floating point data
    Inputs are those for Label, but the default formatStr is "%s" and formatFunc is forbidden.
    """
    def __init__ (self,
        master,
        helpText = None,
        helpURL = None,
        isCurrent = True,
        **kargs
    ):
        kargs.setdefault("formatStr", "%d")
        assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__
        
        Label.__init__(self,
            master,
            helpText = helpText,
            helpURL = helpURL,
            isCurrent = isCurrent,
        **kargs)


class FloatLabel(Label):
    """Label to display floating point data.
    
    If you specify a format string, that is used and the specified is ignored
    else you must specify a precision, in which case the data is displayed
    as without an exponent and with "precision" digits past the decimal.
    The default precision is 2 digits.
    
    Inputs:
    - precision: number of digits past the decimal point; ignored if formatStr specified
    The other inputs are those for Label but formatFunc is forbidden.
    """
    def __init__ (self,
        master,
        formatStr=None,
        precision=2,
        helpText = None,
        helpURL = None,
        isCurrent = True,
    **kargs):
        assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__

        # handle default format string
        if formatStr == None:
            formatStr = "%." + str(precision) + "f"
            
        # test and set format string
        try:
            formatStr % (1.1,)
        except:
            raise ValueError, "Invalid floating point format string %s" % (formatStr,)

        Label.__init__(self,
            master,
            formatStr = formatStr,
            helpText = helpText,
            helpURL = helpURL,
            isCurrent = isCurrent,
        **kargs)


class DMSLabel(Label):
    """Label to display floating point data as dd:mm:ss.ss.
    Has the option to store data in degrees but display in hh:mm:ss.ss;
    this option can be changed at any time and the display updates correctly.
    
    Inputs:
    - precision: number of digits past the decimal point
    - nFields: number of sexagesimal fields to display
    - cnvDegToHrs: if True, data is in degrees but display is in hours
    The other inputs are those for Label, but formatStr and formatFunc are forbidden.
    """
    def __init__ (self,
        master,
        precision,
        nFields = 3,
        cvtDegToHrs = False,
        helpText = None,
        helpURL = None,
        isCurrent = True,
    **kargs):
        assert not kargs.has_key("formatStr"), "formatStr not allowed for %s" % self.__class__.__name__
        assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__
        
        self.precision = precision
        self.nFields = nFields
        self.cvtDegToHrs = cvtDegToHrs

        Label.__init__(self,
            master,
            formatFunc = self.formatFunc,
            helpText = helpText,
            helpURL = helpURL,
            isCurrent = isCurrent,
        **kargs)
    
    def formatFunc(self, value):
        if self.cvtDegToHrs and value != None:
            value = value / 15.0
        return RO.StringUtil.dmsStrFromDeg (
            value,
            precision = self.precision,
            nFields = self.nFields,
        )
    
    def setCvtDegToHrs(self, cvtDegToHrs):
        if RO.MathUtil.logNE(self.cvtDegToHrs, cvtDegToHrs):
            self.cvtDegToHrs = cvtDegToHrs
            self._updateText()


if __name__ == "__main__":
    import PythonTk
    root = PythonTk.PythonTk()

    wdgSet = (
        BoolLabel(root,
            helpText = "Bool label",
        ),
        StrLabel(root,
            helpText = "String label",
        ),
        IntLabel(root,
            width=5,
            helpText = "Int label; width=5",
        ),
        FloatLabel(root,
            precision=2,
            width=5,
            helpText = "Float label; precision = 2, width=5",
        ),
        FloatLabel(root,
            formatStr="%.5g",
            width=8,
            helpText = "Float label; format = '\%.5g', width = 8",
        ),
        DMSLabel(root,
            precision=2,
            width=10,
            helpText = "DMS label; precision = 2, width = 10",
        ),
        DMSLabel(root,
            precision=2,
            cvtDegToHrs=1,
            width=10,
            helpText = "DMS label; precision = 2, width = 10, convert degrees to hours",
        ),
    )
    for wdg in wdgSet:
        wdg.pack(fill=Tkinter.X)
    
    # a list of (value, isCurrent) pairs
    testData = [
        ("some text", True),
        ("invalid text", False),
        (0, True),
        ("", True),
        (False, True),
        (1, True),
        (1234567890, True),
        (1234567890, False),
        (1.1, True),
        (1.9, True),
        (-1.1, True),
        (-1.9, True),
        (-0.001, True),
        (-1.9, False),
    ]
    
    ind = 0
    def displayNext():
        global ind, testData
        val = testData[ind]
        print "\nvalue = %r, isCurrent = %s" % tuple(val)
        for wdg in wdgSet:
            wdg.set(*val)
        ind += 1
        if ind < len(testData):
            root.after(1200, displayNext)
    root.after(1200, displayNext)
            
    root.mainloop()
