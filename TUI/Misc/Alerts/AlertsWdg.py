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
        self.actor, self.keyword = self.alertID.split(".", 1)
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
        )


class DisabledInfo(object):
    """Information about a disabled alert (from the alertDisabled keyword).
    
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
#         print "DisabledInfo=", self

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
        
        row = 0
        maxCols = 5
        
#         currFrame = Tkinter.Frame(self)
#         Tkinter.Label(currFrame, text="Current Alerts").pack(side="left")
#         currFrame.grid(row=row, column=0, columnspan=maxCols, sticky="w")
#         row += 1
        
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
        self.disabledToggleWdg = RO.Wdg.Checkbutton(
            master = disabledFrame,
            text = "No Disabled Alerts",
            callFunc = self._doShowHideDisabledAlerts,
            indicatoron = False,
            helpText = "show/hide disabled alerts",
        )
        self.disabledToggleWdg.pack(side="left")
        disabledFrame.grid(row=row, column=0, columnspan=maxCols, sticky="w")
        row += 1

        self.disabledWdg = RO.Wdg.LogWdg(
            master = self,
            helpText = "disabled alerts",
            helpURL = _HelpURL,
            height = 5,
        )
        self.disabledWdg.text.ctxSetConfigFunc(self._disabledCtxConfigMenu)
        self.disabledWdg.grid(row=row, column=0, columnspan=maxCols, sticky="news")
        row += 1
        
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            playCmdSounds = False,
        )
        self.statusBar.grid(row=row, column=0, columnspan=maxCols, sticky="ew")
        
        # dictionary of alertInfo.alertID: alertInfo for current alerts
        self.alertsDict = {}
        
        # dictionary of disabledAlertInfo.disabledID: disabledAlertInfo for disabled alerts
        self.disabledDict = {}
        
        self.alertsModel = TUI.Models.AlertsModel.Model()
        self.alertsModel.activeAlerts.addCallback(self._activeAlertsCallback, callNow=False)
        self.alertsModel.disabledAlerts.addCallback(self._disabledAlertsCallback, callNow=False)
        self.alertsModel.alert.addCallback(self._alertCallback, callNow=False)
        
        severityList = self.alertsModel.alert.key.typedValues.vtypes[1].enumLabels
        numSev = len(severityList)
        self.severityOrderDict = dict((sev, numSev-ind) for ind, sev in enumerate(severityList))
        self.severityWidth = max(len(sev) for sev in severityList)

        self._severityPrefDict = RO.Wdg.WdgPrefs.getSevPrefDict()
        for sev, roSev in SeverityDict.iteritems():
            colorPref = self._severityPrefDict[roSev]
            sevTag = "sev_%s" % (sev,)
            if roSev == RO.Constants.sevNormal:
                # normal color is already automatically updated
                # but do make tag known to text widget
                self.alertsWdg.text.tag_configure(sevTag)
                self.disabledWdg.text.tag_configure(sevTag)
                continue
            colorPref.addCallback(RO.Alg.GenericCallback(self._updSevTagColor, sevTag), callNow=True)

        self._doShowHideDisabledAlerts()

    def getIDAtInsertCursor(self, textWdg):
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

    def ackAlert(self, alertID, severity):
        """Acknowledge the specified alert
        
        Inputs:
        - alertID: alert ID as actor.name
        - severity: alert severity
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "alerts",
            cmdStr = "acknowledgeAlert id=%s severity=%s" % (alertID, severity),
        )
        self.statusBar.doCmd(cmdVar)
    
    def enableAlert(self, alertID, severity):
        """Enable the specified alert

        Inputs:
        - alertID: alert ID as actor.name
        - severity: alert severity
        """
        cmdVar = opscore.actor.keyvar.CmdVar(
            actor = "alerts",
            cmdStr = "disableAlert id=%s severity=%s enable=True" % (alertID, severity),
        )
        self.statusBar.doCmd(cmdVar)

    def _alertsCtxConfigMenu(self, menu):
        textWdg = self.alertsWdg.text
        textWdg.ctxConfigMenu(menu)

        alertID = self.getIDAtInsertCursor(textWdg)
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
                    self.ackAlert(alertID, severity)
                menu.add_command(
                    label = "Acknowledge %s" % (alertID),
                    command = menuFunc,
                )
        return True
        
    def _disabledCtxConfigMenu(self, menu):
        textWdg = self.disabledWdg.text
        textWdg.ctxConfigMenu(menu)

        disabledID = self.getIDAtInsertCursor(textWdg)
        if disabledID:
            disabledInfo = self.disabledDict.get(disabledID)
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
    
    def _getInfo(self):
        """Get status if there are any unknown alerts"""
        needInfo = False
        for alertInfo in self.alertsDict.itervalues():
            if alertInfo.isUnknown:
                needInfo = True
                break
        if needInfo:
            cmdVar = opscore.actor.keyvar.CmdVar(
                actor = "alerts",
                cmdStr = "status",
            )
            self.statusBar.doCmd(cmdVar)
    
    def _activeAlertsCallback(self, keyVar):
        didChange = False
        currAlertIDs = set(keyVar.valueList)
        oldAlertIDs = set(self.alertsDict.keys())
        if currAlertIDs == oldAlertIDs:
#             print "activeAlerts seen and my info is current"
            return

        needInfo = False
        for deadAlertID in oldAlertIDs - currAlertIDs:
            del(self.alertsDict[deadAlertID])
        for newAlertID in currAlertIDs - oldAlertIDs:
            needInfo = True
            self.alertsDict[newAlertID] = AlertInfo(newAlertID)
        if needInfo:
            self.tuiModel.reactor.callLater(0.5, self._getInfo)
        self._updateAlerts()
        
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
        self._updateAlerts()
    
    def _disabledAlertsCallback(self, keyVar):
#         print "_disabledAlertsCallback(%s)" % (keyVar,)
        if not keyVar.isCurrent:
            return
        if len(keyVar.valueList) > 0 and keyVar[0] == None:
            return
        self.disabledDict.clear()
        idSevList = [re.split(r", *", val[1:-1]) for val in keyVar.valueList]
            
        for id, sev in idSevList:
            disabledInfo = DisabledInfo(id, sev)
            self.disabledDict[disabledInfo.disabledID] = disabledInfo
        self._updateDisabled()
    
    def _doShowHideDisabledAlerts(self, wdg=None):
        doShow = self.disabledToggleWdg.getBool()
        if doShow:
            self.disabledWdg.grid()
        else:
            self.disabledWdg.grid_remove()
    
    def _updateAlerts(self):
        alertList = []
        for alertInfo in self.alertsDict.itervalues():
            sevOrder = self.severityOrderDict.get(alertInfo.severity, 99)
            alertList.append(
                ((sevOrder, alertInfo.alertID), alertInfo)
            )
        alertList.sort()
        self.alertsWdg.clearOutput()
        for sortKey, alertInfo in alertList:
            msgStr = "%s \t%s %s" % (alertInfo.severity.title(), alertInfo.alertID, alertInfo.value)
            if alertInfo.isAcknowledged:
                msgStr = "[%s]" % (msgStr,)
            self.alertsWdg.addMsg(msgStr, tags=alertInfo.tags)

    def _updateDisabled(self):
        disbledAlertList = []
        for alertInfo in self.disabledDict.itervalues():
            sevOrder = self.severityOrderDict.get(alertInfo.severity, 99)
            disbledAlertList.append(
                ((sevOrder, alertInfo.alertID), alertInfo)
            )
        disbledAlertList.sort()
        self.disabledWdg.clearOutput()
        for sortKey, alertInfo in disbledAlertList:
            msgStr = "%s \t%s" % (alertInfo.severity.title(), alertInfo.alertID)
            self.disabledWdg.addMsg(msgStr, tags=alertInfo.tags)

        numDisabled = len(self.disabledDict)
        severity = RO.Constants.sevWarning
        if numDisabled == 0:
            btnStr = "No Disabled Alerts"
            severity = RO.Constants.sevNormal
        elif numDisabled == 1:
            btnStr = "1 Disabled Alert"
        else:
            btnStr = "%d Disabled Alerts" % (numDisabled,)
        self.disabledToggleWdg["text"] = btnStr
        self.disabledToggleWdg.setSeverity(severity)

    def _updSevTagColor(self, sevTag, color, colorPref):
        """Apply the current color appropriate for the current severity.
        """
        #print "_updSevTagColor(sevTag=%r, color=%r, colorPref=%r)" % (sevTag, color, colorPref)
        self.alertsWdg.text.tag_configure(sevTag, foreground=color)
        self.disabledWdg.text.tag_configure(sevTag, foreground=color)

if __name__ == '__main__':
    import TestData
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot

    testFrame = AlertsWdg(root)
    testFrame.pack(expand=1, fill="both")

    Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
    
    TestData.start()

    tuiModel.reactor.run()
