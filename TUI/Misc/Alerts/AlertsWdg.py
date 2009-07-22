#!/usr/bin/env python
"""Alerts widget

Want to save ack state somewhere, somehow -- and display it.
Also display a checkbox for ack and maybe disabled.

Also, when an alert goes away, I should display it with a line through it for a minute.

History:
2009-07-22 ROwen    Started work
"""
import time
import Tkinter
import RO.Wdg
import RO.Wdg.WdgPrefs
import TUI.Models.TUIModel
import TUI.Models.AlertsModel

_HelpURL = None # "Misc/AlertsWin.html"

# dictionary of alert severity (lowercase), RO.Const severity
SeverityDict = dict(
    info = RO.Constants.sevNormal,
    warn = RO.Constants.sevWarning,
    serious = RO.Constants.sevError,
    critical = RO.Constants.sevError,
)

SeverityOrderDict = dict(
    info = 4,
    warn = 3,
    serious = 2,
    critical = 1,
)

class AlertInfo(object):
    """
    Fields include:
    - alertID: unique ID for this alert = <actor>.<severity>
    - actor
    - severity
    - isEnabled
    - timestamp
    """
    def __init__(self, keyVar):
        self.id, self.severity, self.value, self.isEnabled = keyVar.valueList
        self.actor, self.keyword = self.id.split(".", 1)
        self.timestamp = time.time()
    
    def __eq__(self, rhs):
        """Two alertInfos are considered equal if all data except timestamp match.
        """
        if not isinstance(rhs, self.__class__):
            return False
        return self.id == rhs.id \
            and self.severity == rhs.severity \
            and self.value == rhs.value \
            and self.isEnabled == rhs.isEnabled

    def __str__(self):
        return "%s %s %s %s" % (self.id, self.severity, self.value, self.isEnabled)
    
    @property
    def isDone(self):
        """Return True if alert can be removed, meaning severity=info
        """
        return self.severity == "info"

    @property
    def tags(self):
        """Return tags used for displaying the data in a Tkinter Text widget.
        """
        return ("act_%s" % (self.actor,), "sev_%s" % (self.severity,))


class AlertEnabledInfo(object):
    """Information about an alertEnable
    
    Fields include:
    - id: (alertID, severity): unique ID for this alertEnabled
        There can be more than one alertEnabled for a given alert,
        so alertEnabledInfo.id is NOT the same as AlertInfo.id.
    - alertID: see AlertInfo
    - severity
    - isEnabled
    - timestamp
    """
    def __init__(self, keyVar):
        self.alertID, self.severity, self.isEnabled = keyVar.valueList
        self.id = (self.alertID, self.severity)
        self.timestamp = time.time()

    def __eq__(self, rhs):
        """Two alertEnabledInfos are considered equal if all data except timestamp match.
        """
        if not isinstance(rhs, self.__class__):
            return False
        return self.id == rhs.id \
            and self.isEnabled == rhs.isEnabled

    def __str__(self):
        return "%s %s %s %s" % (self.alertID, self.severity, self.isEnabled)


class AlertsWdg(Tkinter.Frame):
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)
        
        self.logWdg = RO.Wdg.LogWdg(
            master = self,
#            helpText = None,
            helpURL = _HelpURL,
        )
        self.logWdg.grid(row=1, column=0, columnspan=5, sticky="news")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(4, weight=1)
        
        # dictionary of alertInfo.id: alertInfo
        self.alertsDict = {}
        
        # dictionary of enabledAlertInfo.id: enabledAlertInfo
        self.enabledDict = {}
        
        self.alertsModel = TUI.Models.AlertsModel.Model()
        self.alertsModel.alert.addCallback(self._alertCallback, callNow=False)
        self.alertsModel.alertEnabled.addCallback(self._alertEnabledCallback, callNow=False)
        
        severityList = self.alertsModel.alert.key.typedValues.vtypes[1].enumLabels
        self.severityWidth = max(len(sev) for sev in severityList)

        self._severityPrefDict = RO.Wdg.WdgPrefs.getSevPrefDict()
        for sev, roSev in SeverityDict.iteritems():
            colorPref = self._severityPrefDict[roSev]
            sevTag = "sev_%s" % (sev,)
            if roSev == RO.Constants.sevNormal:
                # normal color is already automatically updated
                # but do make tag known to text widget
                self.logWdg.text.tag_configure(sevTag)
                continue
            colorPref.addCallback(RO.Alg.GenericCallback(self._updSevTagColor, sevTag), callNow=True)

    def _alertCallback(self, keyVar):
#         print "_alertCallback(%s)" % (keyVar,)
        if not keyVar.isCurrent:
            return
        newAlertInfo = AlertInfo(keyVar)
        # if already present, ignore the change
        oldAlertInfo = self.alertsDict.get(newAlertInfo.id)
        if oldAlertInfo == newAlertInfo:
#             print "ignoring repeat of existing alert:", oldAlertInfo
            return
        if newAlertInfo.isDone:
            del(self.alertsDict[newAlertInfo.id])
        else:
            self.alertsDict[newAlertInfo.id] = newAlertInfo
        self.update()
    
    def _alertEnabledCallback(self, keyVar):
#         print "_alertEnabledCallback(%s)" % (keyVar,)
        if not keyVar.isCurrent:
            return
        newAlertEnabled = AlertEnabled(keyVar)
        # if already known, then ignore the change
        oldAlertEnabled = self.alertsDict.get(newAlertEnabled.id)
        if oldAlertEnabled == newAlertEnabled:
#             print "ignoring repeat of existing alertEnabled:", oldAlertEnabled
            return
        if newAlertEnabled.isEnabled:
            del(self.alertsDict[newAlertEnabled.id])
        else:
            self.alertsDict[newAlertEnabled.id] = newAlertEnabled
        self.update()

    def update(self):
        alertList = []
        for alertInfo in self.alertsDict.itervalues():
            sevOrder = SeverityOrderDict.get(alertInfo.severity, 99)
            alertList.append(
                ((sevOrder, alertInfo.id), alertInfo)
            )
        alertList.sort()
        self.logWdg.clearOutput()
        for sortKey, alertInfo in alertList:
            msgStr = "%s \t%s %s" % (alertInfo.severity.title(), alertInfo.id, alertInfo.value)
            self.logWdg.addMsg(msgStr, tags=alertInfo.tags)

    def _updSevTagColor(self, sevTag, color, colorPref):
        """Apply the current color appropriate for the current severity.
        
        Called automatically. Do NOT call manually.
        """
        #print "_updSevTagColor(sevTag=%r, color=%r, colorPref=%r)" % (sevTag, color, colorPref)
        self.logWdg.text.tag_configure(sevTag, foreground=color)

if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot

    testFrame = AlertsWdg(root)
    testFrame.pack(expand=1, fill="both")

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()
