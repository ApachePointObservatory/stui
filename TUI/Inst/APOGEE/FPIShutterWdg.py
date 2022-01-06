#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-01-06
# @Filename: FPIShutterWdg.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import RO.Constants
import RO.Wdg
import TUI.Models
import BaseDeviceWdg


class FPIShutterWdg(BaseDeviceWdg.BaseDeviceWdg):
    """Widgets to control APOGEE's FPI shutter."""

    _ShutterCat = "shutter"

    def __init__(self, gridder, statusBar, colSpan=3, helpURL=None):

        BaseDeviceWdg.BaseDeviceWdg.__init__(self,
            master = gridder._master,
            actor = "apogeefpi",
            statusBar = statusBar,
            helpURL = helpURL,
        )
        self._updatingStatus = False

        self.statusBar = statusBar
        self.helpURL = helpURL

        self.gridder = gridder
        master = self.gridder._master

        self.openCloseWdg = RO.Wdg.Checkbutton(
            master = master,
            text = "FPI Shutter",
            callFunc = self._doOpenClose,
            helpText = "Open/close FPI shutter",
            helpURL = helpURL,
        )

        self.summaryWdg = RO.Wdg.StrLabel(
            master = master,
            anchor = "w",
            helpText = "Shutter status",
            helpURL = helpURL,
        )
        gridder.gridWdg(self.openCloseWdg, self.summaryWdg, sticky="w", colSpan=colSpan)

        self.model = TUI.Models.getModel("apogeefpi")
        self.model.shutter_position.addCallback(self._updSummary)

    def _doOpenClose(self, wdg=None):
        """Open/closes the shutter."""

        status = self.openCloseWdg.getBool()
        if status is False:
            self.doCmd("close")
        else:
            self.doCmd("open")

    def _updSummary(self, *dumArgs):
        """Update FPI shutter summary label."""

        severity = RO.Constants.sevError
        sumStr = "Unknown"
        isCurrent = self.model.shutter_position.isCurrent

        if self.model.shutter_position[0] == "open":
            sumStr = "Open"
            severity = RO.Constants.sevNormal
        elif self.model.shutter_position[0] == "closed":
            sumStr = "Closed"
            severity = RO.Constants.sevNormal
        else:
            severity = RO.Constants.sevError
            sumStr = "Unknown"

        self.summaryWdg.set(sumStr, isCurrent=isCurrent, severity=severity)
