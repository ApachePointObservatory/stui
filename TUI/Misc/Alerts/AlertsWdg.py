#!/usr/bin/env python
"""Alerts widget

To do:
- Show timestamp and/or age of an alert -- but how without clutter?
- When an alert goes away, display it with a line through it for a minute,
  or something similar. Unfortunately I am already using strikethrough for disabled.
- When a critical alert arrives play a sound and flash the alert
- Flash any new alert.
  (Note that timestamps make it easy to identify when to stop flashing new alerts)

History:
2009-07-23 ROwen
"""
import re
import sys
import time
import opscore.actor
import Tkinter
import SimpleDialog
import RO.Wdg
import RO.Wdg.WdgPrefs
import TUI.Models.TUIModel
import TUI.Models.AlertsModel
import TUI.Base.Wdg

_HelpURL = None # "Misc/AlertsWin.html"

CmdTimeLimit = 2.5 # command time limit

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
    
    Inputs:
    - alertID: unique ID for this alert = <actor>.<severity>
    - severity: severity of alert
    - value: value of alert
    - isEnabled: is the alert enabled?
    - isAcknowledged: has the alert been acknowledged?
    
    Note that the inputs are in the right order that you can construct
    from an alert KeyVar using: AlertInfo(*alertKeyVar.values)
    
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
    """Information about a disabled alert rule (from the disabledAlertRule keyword).
    
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

        # dictionary of alertInfo.alertID: alertInfo for current alerts
        self.alertDict = {}
        
        # dictionary of disableRule.disabledID: disableRule for disabled alert rules
        self.ruleDict = {}
        
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
        self.addRuleWdg = RO.Wdg.Button(
            master = disabledFrame,
            text = "Add Rule",
            callFunc = self.addAlertDisableRule,
            helpText = "add a new alert disable rule",
        )
        self.addRuleWdg.pack(side="left")
        disabledFrame.grid(row=row, column=0, columnspan=maxCols, sticky="w")
        row += 1

        self.rulesWdg = RO.Wdg.LogWdg(
            master = self,
            helpText = "Disabled alert rules",
            helpURL = _HelpURL,
            height = 5,
        )
        self.rulesWdg.text.ctxSetConfigFunc(self._ruleCtxConfigMenu)
        self.rulesWdg.grid(row=row, column=0, columnspan=maxCols, sticky="news")
        row += 1
        
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = True,
        )
        self.statusBar.grid(row=row, column=0, columnspan=maxCols, sticky="ew")
        
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

    def sendAlertCmd(self, cmdVerb, alertID, severity, doConfirm=False):
        """Send an alert command of the form <verb> id=alertID, severity=severity
        
        Inputs:
        - cmdVerb: may be one of acknowledge, noacknowledge, enable, disable
        - alertID: alert ID in the form actor.alertName
        - severity: alert severity, e.g. "serious", etc.
        """
        if doConfirm:
            dialog = SimpleDialog.SimpleDialog(self,
                text="Really %s %s %s?" % (cmdVerb, alertID, severity),
                buttons=["Yes", "No"],
                default=0,
                cancel=1,
                title="Test Dialog")
            if dialog.go() > 0:
                return
            
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "alerts",
            cmdStr = "%s id=%s severity=%s" % (cmdVerb, alertID, severity),
            timeLim = CmdTimeLimit,
        )
        self.statusBar.doCmd(cmdVar)

    def addAlertDisableRule(self, wdg=None):
        """Add a new alert disable rule, using a dialog box for input.
        """
        d = NewRuleDialog(self)
        if d.result == None:
            return
        if "" in d.result:
            print "self.statusBar.cmdFailedSound=", self.statusBar.cmdFailedSound
            self.statusBar.playCmdFailed()
            self.statusBar.setMsg("Actor and/or keyword missing", severity=RO.Constants.sevError)
            return
        actor, keyword, severity = d.result
        alertID = "%s.%s" % (actor, keyword)
        self.sendAlertCmd("disable", alertID, severity.lower())

    def displayActiveAlerts(self):
        alertList = []
        for alertInfo in self.alertDict.itervalues():
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
        for alertInfo in self.ruleDict.itervalues():
            sevOrder = self.severityOrderDict.get(alertInfo.severity, 99)
            ruleList.append(
                ((sevOrder, alertInfo.alertID), alertInfo)
            )
        ruleList.sort()
        self.rulesWdg.clearOutput()
        for sortKey, alertInfo in ruleList:
            msgStr = "%s \t%s" % (alertInfo.severity.title(), alertInfo.alertID)
            self.rulesWdg.addMsg(msgStr, tags=alertInfo.tags)

        numDisabled = len(self.ruleDict)
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
    
    def _alertsCtxConfigMenu(self, menu):
        textWdg = self.alertsWdg.text
        textWdg.ctxConfigMenu(menu)

        alertID = self._getIDAtInsertCursor(textWdg)
        if alertID:
            alertInfo = self.alertDict.get(alertID)
            if not alertInfo:
                sys.stderr.write("bug: alertID=%s selected for ack but not found in dict\n" % (alertID,))
                return True
            menu.add_separator()
            if alertInfo.isUnknown:
                menu.add_command(
                    label = "(Unknown %s)" % (alertID),
                    state = "disabled",
                )
                return True
            if alertInfo.isAcknowledged:
                def menuFunc(self=self, alertID=alertInfo.alertID, severity=alertInfo.severity):
                    self.sendAlertCmd("unacknowledge", alertID, severity)
                menu.add_command(
                    label = "UnAcknowledge %s" % (alertID),
                    command = menuFunc,
                )
            else:
                def menuFunc(self=self, alertID=alertInfo.alertID, severity=alertInfo.severity):
                    self.sendAlertCmd("acknowledge", alertID, severity)
                menu.add_command(
                    label = "Acknowledge %s" % (alertID),
                    command = menuFunc,
                )
            menu.add_separator()
            if alertInfo.isEnabled:
                def menuFunc(self=self, alertID=alertInfo.alertID, severity=alertInfo.severity):
                    self.sendAlertCmd("disable", alertID, severity, doConfirm=True)
                menu.add_command(
                    label = "Disable %s" % (alertID),
                    command = menuFunc,
                )
            else:
                def menuFunc(self=self, alertID=alertInfo.alertID, severity=alertInfo.severity):
                    self.sendAlertCmd("enable", alertID, severity)
                menu.add_command(
                    label = "Enable %s" % (alertID),
                    command = menuFunc,
                )
        return True
        
    def _ruleCtxConfigMenu(self, menu):
        textWdg = self.rulesWdg.text
        textWdg.ctxConfigMenu(menu)

        disabledID = self._getIDAtInsertCursor(textWdg)
        if disabledID:
            disabledInfo = self.ruleDict.get(disabledID)
            if not disabledInfo:
                sys.stderr.write("bug: disabledID=%s selected for enable but not found in dict\n" % (disabledID,))
                return True
            menu.add_separator()
            def menuFunc(self=self, alertID=disabledInfo.alertID, severity=disabledInfo.severity):
                self.sendAlertCmd("enable", alertID, severity)
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
            timeLim = CmdTimeLimit,
        )
        self.statusBar.doCmd(self._statusCmd)
    
    def _needStatus(self):
        """Return True if active alert info dict includes alerts with unknown values.
        
        The need for alert info is expected at first connection time; activeAlerts is read from cache,
        but information about those alerts is not available from the cache. So I end up with a list of
        active alerts, but no information about them.
        """
        needInfo = False
        for alertInfo in self.alertDict.itervalues():
            if alertInfo.isUnknown:
                needInfo = True
                break
        return needInfo

    def _activeAlertsCallback(self, keyVar):
        didChange = False
        currAlertIDs = set(keyVar)
        oldAlertIDs = set(self.alertDict.keys())
        if currAlertIDs == oldAlertIDs:
#             print "activeAlerts seen and my info is current"
            return

        for deadAlertID in oldAlertIDs - currAlertIDs:
            del(self.alertDict[deadAlertID])
        for newAlertID in currAlertIDs - oldAlertIDs:
            self.alertDict[newAlertID] = AlertInfo(newAlertID)
        
        if not self._statusCmdRunning() and self._needStatus():
            self.tuiModel.reactor.callLater(0.5, self._getStatus)
        self.displayActiveAlerts()

    def _alertCallback(self, keyVar):
#         print "_alertCallback(%s)" % (keyVar,)
        if not keyVar.isCurrent:
            return
        newAlertInfo = AlertInfo(*keyVar)
        # if this alert (with matching value, severity and ID) already exists, then ignore the change
        oldAlertInfo = self.alertDict.get(newAlertInfo.alertID)
        if oldAlertInfo == newAlertInfo:
#             print "ignoring repeat of existing alert:", oldAlertInfo
            return
        if newAlertInfo.isDone and oldAlertInfo:
            del(self.alertDict[newAlertInfo.alertID])
        else:
            self.alertDict[newAlertInfo.alertID] = newAlertInfo
        self.displayActiveAlerts()
    
    def _disabledAlertRulesCallback(self, keyVar):
#         print "_disabledAlertRulesCallback(%s)" % (keyVar,)
        if not keyVar.isCurrent:
            return
        self.ruleDict.clear()
        idSevList = []
        for val in keyVar:
            if val == None:
                continue
            try:
                alertID, severity = re.split(r", *", val[1:-1])
            except Exception, e:
                sys.stderr.write("Cannot parse %s as (alertID, severity)\n" % (val,))
            disabledInfo = DisableRule(alertID, severity)
            self.ruleDict[disabledInfo.disabledID] = disabledInfo
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

class NewRuleDialog(RO.Wdg.InputDialog.ModalDialogBase):
    """Ask user for information for a new alert disable rule.
    
    self.result = actor, keyword, severity (or None if cancelled)
    """
    def __init__(self, master):
        RO.Wdg.InputDialog.ModalDialogBase.__init__(self, master, "New Rule")

    def body(self, master):
        gr = RO.Wdg.Gridder(master, sticky="ew")
        
        self.actorWdg = RO.Wdg.StrEntry(
            master = master,
        )
        gr.gridWdg("Actor", self.actorWdg)
        self.keywordWdg = RO.Wdg.StrEntry(
            master = master,
        )
        gr.gridWdg("Keyword", self.keywordWdg)
        alertsModel = TUI.Models.AlertsModel.Model()
        severityList = [val.title() for val in alertsModel.alert.key.typedValues.vtypes[1].enumLabels if val != "ok"]
        severityList.reverse()
        self.severityWdg = RO.Wdg.OptionMenu(
            master = master,
            items = severityList,
            defValue = "Critical",
        )
        gr.gridWdg("Severity", self.severityWdg)
        return self.actorWdg # initial focus

    def setResult(self):
        first = self.actorWdg.get()
        second = self.keywordWdg.get()
        third = self.severityWdg.getString()
        self.result = (first, second, third)



if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    
    testFrame = AlertsWdg(root)
    testFrame.pack(expand=1, fill="both")

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()
