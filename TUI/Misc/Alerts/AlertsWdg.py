#!/usr/bin/env python
"""Alerts widget

To do:
- Allow user to acknowledge an alert, probably with a right click
- Show timestamp of alert -- but how without clutter?
  (Could show age, but don't update 1/second)
- Allow user to enable/disable an alert (don't make disable too easy)
- When an alert goes away, display it with a line through it for a minute.
- When a critical alert arrives play a sound and flash the alert
- Flash any new alert.
(Note that timestamps make it easy to identify when to stop flashing new alerts)

History:
2009-07-22 ROwen    Started work
"""
import re
import sys
import time
import opscore.actor
import Tkinter
import RO.Wdg
import RO.Wdg.WdgPrefs
import TUI.Models.TUIModel
import TUI.Models.AlertsModel
import TUI.Base.Wdg

_HelpURL = None # "Misc/AlertsWin.html"

# dictionary of alert severity (lowercase), RO.Const severity
SeverityDict = {
    "ok": RO.Constants.sevNormal,
    "info": RO.Constants.sevNormal,
    "warn": RO.Constants.sevWarning,
    "serious": RO.Constants.sevError,
    "critical": RO.Constants.sevError,
    "?":  RO.Constants.sevWarning,
}

class AlertInfo(object):
    """Information about an alert (from the alert keyword).
    
    Fields include:
    - alertID: unique ID for this alert = <actor>.<severity>
    - actor
    - severity
    - isEnabled
    - isAcknowledged
    - timestamp
    """
    def __init__(self,
        alertID,
        severity = "?",
        value = "?",
        isEnabled = True,
        isAcknowledged = False,
    ):
        self.alertID = alertID
        self.severity = severity.lower()
        self.value = value
        self.isEnabled = bool(isEnabled)
        self.isAcknowledged = bool(isAcknowledged)
        try:
            self.actor, self.keyword = self.alertID.split(".", 1)
        except Exception, e:
            sys.stderr.write("Cannot parse %s as actor.keyword\n" % (self.alertID,))
            self.actor = "?"
            self.keyword = "?"
        self.timestamp = time.time()
#         print "AlertInfo=", self
    
    def __eq__(self, rhs):
        """Two alertInfos are considered equal if all data except the timestamp match.
        """
        if not isinstance(rhs, self.__class__):
            return False
        return self.alertID == rhs.alertID \
            and self.severity == rhs.severity \
            and self.value == rhs.value \
            and self.isEnabled == rhs.isEnabled \
            and self.isAcknowledged == rhs.isAcknowledged

    def __str__(self):
        enabledStr = "Enabled" if self.isEnabled else "Disabled"
        ackedStr = "Ack" if self.isAcknowledged else "NoAck"
        return "%s %s %s %s %s" % (self.alertID, self.severity, self.value, enabledStr, ackedStr)
    
    @property
    def isDone(self):
        """Return True if alert can be removed, meaning severity=ok
        """
        return self.severity == "ok"
    
    @property
    def isUnknown(self):
        """Return True if alert info is unknown"""
        return self.severity == "?"

    @property
    def tags(self):
        """Return tags used for displaying the data in a Tkinter Text widget.
        """
        return (
            "id_%s" % (self.alertID,),
            "sev_%s" % (self.severity,),
            "en_%s" % (self.isEnabled,),
            "ack_%s" % (self.isAcknowledged,),
        )


class DisableRule(object):
    """Information about a disabled alert rule
    
    Fields include:
    - disabledID: a string: "(alertID,severity)": unique ID for this disabled alert
        (it is a string, rather than a tuple, so that it can be used as a tk tag)
    - alertID: see AlertInfo
    - severity
    - isDisabled
    - timestamp
    """
    def __init__(self, alertID, severity):
        self.alertID = alertID
        self.severity = severity.lower()
        self.actor = self.alertID.split(".")
        self.disabledID = "(%s,%s)" % (self.alertID, self.severity)
        self.timestamp = time.time()
#         print "DisableRule=", self

    def __eq__(self, rhs):
        """Two DisabledInfos are considered equal if all data except timestamp match.
        """
        if not isinstance(rhs, self.__class__):
            return False
        return self.disabledID == rhs.disabledID \
            and self.isDisabled == rhs.isDisabled

    def __str__(self):
        return "%s: %s %s" % (self.disabledID, self.alertID, self.severity)

    @property
    def tags(self):
        """Return tags used for displaying the data in a Tkinter Text widget.
        """
        return (
            "id_%s" % (self.disabledID),
            "sev_%s" % (self.severity,),
        )

class AlertsWdg(Tkinter.Frame):
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)
        
        self.tuiModel = TUI.Models.TUIModel.Model()
        self._statusCmd = None
        
        row = 0
        maxCols = 5
        
        activeFrame = Tkinter.Frame(self)
        RO.Wdg.StrLabel(
            master = activeFrame,
            text = "Active Alerts ",
        ).pack(side="left"),
        self.disabledAlertsShowHideWdg = RO.Wdg.Checkbutton(
            master = activeFrame,
            callFunc = self._doShowHideDisabledAlerts,
            indicatoron = False,
            helpText = "show/hide active alerts that are disabled",
        )
        self.disabledAlertsShowHideWdg.pack(side="left")
        activeFrame.grid(row=row, column=0, columnspan=maxCols, sticky="w")
        row += 1

        self.alertsWdg = RO.Wdg.LogWdg(
            master = self,
            helpText = "current alerts",
            helpURL = _HelpURL,
        )
        self.alertsWdg.grid(row=row, column=0, columnspan=maxCols, sticky="news")
        self.grid_rowconfigure(row, weight=1)
        self.grid_columnconfigure(maxCols-1, weight=1)
        self.alertsWdg.text.ctxSetConfigFunc(self._alertsCtxConfigMenu)
        row += 1
        
        disabledFrame = Tkinter.Frame(self)
        self.disableRulesShowHideWdg = RO.Wdg.Checkbutton(
            master = disabledFrame,
            callFunc = self._doShowHideDisableRules,
            indicatoron = False,
            helpText = "show/hide disabled alert rules",
        )
        self.disableRulesShowHideWdg.pack(side="left")
        disabledFrame.grid(row=row, column=0, columnspan=maxCols, sticky="w")
        row += 1

        self.rulesWdg = RO.Wdg.LogWdg(
            master = self,
            helpText = "Disabled alert rules",
            helpURL = _HelpURL,
            height = 5,
        )
        self.rulesWdg.text.ctxSetConfigFunc(self._disabledCtxConfigMenu)
        self.rulesWdg.grid(row=row, column=0, columnspan=maxCols, sticky="news")
        row += 1
        
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = False,
        )
        self.statusBar.grid(row=row, column=0, columnspan=maxCols, sticky="ew")
        
        # dictionary of alertInfo.alertID: alertInfo for current alerts
        self.alertsDict = {}
        
        # dictionary of disabledAlertInfo.disabledID: disabledAlertInfo for disabled alerts
        self.disableRuleDict = {}
        
        self.alertsModel = TUI.Models.AlertsModel.Model()
        self.alertsModel.activeAlerts.addCallback(self._activeAlertsCallback, callNow=False)
        self.alertsModel.disabledAlertRules.addCallback(self._disabledAlertRulesCallback, callNow=False)
        self.alertsModel.alert.addCallback(self._alertCallback, callNow=False)
        
        severityList = self.alertsModel.alert.key.typedValues.vtypes[1].enumLabels
        numSev = len(severityList)
        self.severityOrderDict = dict((sev, numSev-ind) for ind, sev in enumerate(severityList))
        self.severityWidth = max(len(sev) for sev in severityList)

        self.alertsWdg.text.tag_configure("en_False", overstrike=True)

        self._severityPrefDict = RO.Wdg.WdgPrefs.getSevPrefDict()
        for sev, roSev in SeverityDict.iteritems():
            colorPref = self._severityPrefDict[roSev]
            sevTag = "sev_%s" % (sev,)
            if roSev == RO.Constants.sevNormal:
                # normal color is already automatically updated
                # but do make tag known to text widget
                self.alertsWdg.text.tag_configure(sevTag)
                self.rulesWdg.text.tag_configure(sevTag)
                continue
            colorPref.addCallback(RO.Alg.GenericCallback(self._updSevTagColor, sevTag), callNow=True)

        self._doShowHideDisabledAlerts()
        self._doShowHideDisableRules()
        self.displayActiveAlerts()
        self.displayRules()

    def acknowledgeAlert(self, alertID, severity):
        """Acknowledge the specified alert
        
        Inputs:
        - alertID: alert ID as actor.name
        - severity: alert severity
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "alerts",
            cmdStr = "acknowledge id=%s severity=%s" % (alertID, severity),
        )
        self.statusBar.doCmd(cmdVar)

    def displayActiveAlerts(self):
        alertList = []
        for alertInfo in self.alertsDict.itervalues():
            sevOrder = self.severityOrderDict.get(alertInfo.severity, 99)
            alertList.append(
                ((sevOrder, alertInfo.alertID), alertInfo)
            )
        alertList.sort()
        self.alertsWdg.clearOutput()
        numDisabled = 0
        for sortKey, alertInfo in alertList:
            msgStr = "%s \t%s %s" % (alertInfo.severity.title(), alertInfo.alertID, alertInfo.value)
            if alertInfo.isAcknowledged:
                msgStr = "[%s]" % (msgStr,)
            if not alertInfo.isEnabled:
                numDisabled += 1
            self.alertsWdg.addMsg(msgStr, tags=alertInfo.tags)

        isCurrent = self.alertsModel.activeAlerts.isCurrent and not self._needStatus()
        self.disabledAlertsShowHideWdg.setIsCurrent(isCurrent)
        severity = RO.Constants.sevWarning
        if not isCurrent:
            btnStr = "? Disabled"
            severity = RO.Constants.sevNormal
        elif numDisabled == 0:
            btnStr = "None Disabled"
            severity = RO.Constants.sevNormal
        else:
            btnStr = "%d Disabled" % (numDisabled,)
        self.disabledAlertsShowHideWdg["text"] = btnStr
        self.disabledAlertsShowHideWdg.setSeverity(severity)

    def displayRules(self):
        ruleList = []
        for alertInfo in self.disableRuleDict.itervalues():
            sevOrder = self.severityOrderDict.get(alertInfo.severity, 99)
            ruleList.append(
                ((sevOrder, alertInfo.alertID), alertInfo)
            )
        ruleList.sort()
        self.rulesWdg.clearOutput()
        for sortKey, alertInfo in ruleList:
            msgStr = "%s \t%s" % (alertInfo.severity.title(), alertInfo.alertID)
            self.rulesWdg.addMsg(msgStr, tags=alertInfo.tags)

        numDisabled = len(self.disableRuleDict)
        severity = RO.Constants.sevWarning
        isCurrent = self.alertsModel.disabledAlertRules.isCurrent
        if not isCurrent:
            btnStr = "? Disable Alert Rules"
            severity = RO.Constants.sevNormal
        elif numDisabled == 0:
            btnStr = "No Disable Alert Rules"
            severity = RO.Constants.sevNormal
        elif numDisabled == 1:
            btnStr = "1 Disable Alert Rule"
        else:
            btnStr = "%d Disable Alert Rules" % (numDisabled,)
        self.disableRulesShowHideWdg["text"] = btnStr
        self.disableRulesShowHideWdg.setSeverity(severity)
        self.disableRulesShowHideWdg.setIsCurrent(isCurrent)
    
    def enableAlert(self, alertID, severity):
        """Enable the specified alert

        Inputs:
        - alertID: alert ID as actor.name
        - severity: alert severity
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "alerts",
            cmdStr = "disable id=%s severity=%s enable=True" % (alertID, severity),
        )
        self.statusBar.doCmd(cmdVar)

    def _alertsCtxConfigMenu(self, menu):
        textWdg = self.alertsWdg.text
        textWdg.ctxConfigMenu(menu)

        alertID = self._getIDAtInsertCursor(textWdg)
        if alertID:
            alertInfo = self.alertsDict.get(alertID)
            if not alertInfo:
                sys.stderr.write("bug: alertID=%s selected for ack but not found in dict\n" % (alertID,))
                return True
            menu.add_separator()
            if alertInfo.isAcknowledged:
                menu.add_command(
                    label = "%s acknowledged" % (alertID),
                    state = "disabled",
                )
            else:
                def menuFunc(self=self, alertID=alertInfo.alertID, severity=alertInfo.severity):
                    self.acknowledgeAlert(alertID, severity)
                menu.add_command(
                    label = "Acknowledge %s" % (alertID),
                    command = menuFunc,
                )
        return True
        
    def _disabledCtxConfigMenu(self, menu):
        textWdg = self.rulesWdg.text
        textWdg.ctxConfigMenu(menu)

        disabledID = self._getIDAtInsertCursor(textWdg)
        if disabledID:
            disabledInfo = self.disableRuleDict.get(disabledID)
            if not disabledInfo:
                sys.stderr.write("bug: disabledID=%s selected for enable but not found in dict\n" % (disabledID,))
                return True
            menu.add_separator()
            def menuFunc(self=self, alertID=disabledInfo.alertID, severity=disabledInfo.severity):
                self.enableAlert(alertID, severity)
            menu.add_command(
                label = "Enable %s %s" % (disabledInfo.severity.title(), disabledInfo.alertID),
                command = menuFunc,
            )
        return True

    def _getIDAtInsertCursor(self, textWdg):
        """Get id at cursor (alertID or disabledID, depending on textWdg)
        
        Return alertID or disabledID (as appropriate) or None if not found
        """
        tagNames = textWdg.tag_names("current")
        id = None
        for tn in tagNames:
            if tn.startswith("id_"):
                if id:
                    sys.stderr.write("duplicate id tags: id_%s, %s\n" % (id, tn))
                    return None
                id = tn[3:]
        return id
    
    def _getStatus(self):
        """Get status if there is unknown alert information.
        """
#         print "_getStatus()"
        if not self._needStatus():
#             print "_getStatus: don't need status"
            return
        self._statusCmd = opscore.actor.keyvar.CmdVar(
            actor = "alerts",
            cmdStr = "status",
        )
        self.statusBar.doCmd(self._statusCmd)
    
    def _needStatus(self):
        """Return True if active alert info dict includes alerts with unknown values.
        
        The need for alert info is expected at first connection time; activeAlerts is read from cache,
        but information about those alerts is not available from the cache. So I end up with a list of
        active alerts, but no information about them.
        """
        needInfo = False
        for alertInfo in self.alertsDict.itervalues():
            if alertInfo.isUnknown:
                needInfo = True
                break
        return needInfo

    def _activeAlertsCallback(self, keyVar):
        didChange = False
        currAlertIDs = set(keyVar.valueList)
        oldAlertIDs = set(self.alertsDict.keys())
        if currAlertIDs == oldAlertIDs:
#             print "activeAlerts seen and my info is current"
            return

        for deadAlertID in oldAlertIDs - currAlertIDs:
            del(self.alertsDict[deadAlertID])
        for newAlertID in currAlertIDs - oldAlertIDs:
            self.alertsDict[newAlertID] = AlertInfo(newAlertID)
        
        if not self._statusCmdRunning() and self._needStatus():
            self.tuiModel.reactor.callLater(0.5, self._getStatus)
        self.displayActiveAlerts()

    def _alertCallback(self, keyVar):
#         print "_alertCallback(%s)" % (keyVar,)
        if not keyVar.isCurrent:
            return
        newAlertInfo = AlertInfo(*keyVar.valueList)
        # if this alert (with matching value, severity and ID) already exists, then ignore the change
        oldAlertInfo = self.alertsDict.get(newAlertInfo.alertID)
        if oldAlertInfo == newAlertInfo:
#             print "ignoring repeat of existing alert:", oldAlertInfo
            return
        if newAlertInfo.isDone and oldAlertInfo:
            del(self.alertsDict[newAlertInfo.alertID])
        else:
            self.alertsDict[newAlertInfo.alertID] = newAlertInfo
        self.displayActiveAlerts()
    
    def _disabledAlertRulesCallback(self, keyVar):
#         print "_disabledAlertRulesCallback(%s)" % (keyVar,)
        if not keyVar.isCurrent:
            return
        self.disableRuleDict.clear()
        idSevList = []
        for val in keyVar.valueList:
            if val == None:
                continue
            try:
                alertID, severity = re.split(r", *", val[1:-1])
            except Exception, e:
                sys.stderr.write("Cannot parse %s as (alertID, severity)\n" % (val,))
            disabledInfo = DisableRule(alertID, severity)
            self.disableRuleDict[disabledInfo.disabledID] = disabledInfo
        self.displayRules()
    
    def _doShowHideDisableRules(self, wdg=None):
        doShow = self.disableRulesShowHideWdg.getBool()
        if doShow:
            self.rulesWdg.grid()
        else:
            self.rulesWdg.grid_remove()
    
    def _doShowHideDisabledAlerts(self, wdg=None):
        """Show or hide active alerts that have been disabled"""
        doShow = self.disabledAlertsShowHideWdg.getBool()
        self.alertsWdg.text.tag_configure("en_False", elide=not doShow)
    

    def _statusCmdRunning(self):
        if not self._statusCmd:
            return False
        return not self._statusCmd.isDone

    def _updSevTagColor(self, sevTag, color, colorPref):
        """Apply the current color appropriate for the current severity.
        """
        #print "_updSevTagColor(sevTag=%r, color=%r, colorPref=%r)" % (sevTag, color, colorPref)
        self.alertsWdg.text.tag_configure(sevTag, foreground=color)
        self.rulesWdg.text.tag_configure(sevTag, foreground=color)

if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot

    testFrame = AlertsWdg(root)
    testFrame.pack(expand=1, fill="both")

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()
