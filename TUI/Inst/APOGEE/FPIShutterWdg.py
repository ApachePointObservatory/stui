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

        self.shutterWdg = RO.Wdg.Checkbutton(
            master = master,
            onvalue = "Open",
            offvalue = "Closed",
            autoIsCurrent = True,
            showValue = True,
            callFunc = self.doShutter,
            helpText = "Open or close FPI shutter",
            helpURL = helpURL,
        )

        gridder.gridWdg("FPI Shutter", self.shutterWdg, self.cancelBtn, sticky="w")

        self.model = TUI.Models.getModel(self.actor)
        self.model.shutter_position.addCallback(self.updateStatus)

    def doShutter(self, wdg=None):
        """Send a command to open or close the shutter
        """
        doOpen = self.shutterWdg.getBool()
        if doOpen:
            cmdStr = "open"
        else:
            cmdStr = "close"
        self.doCmd(cmdStr)

    def enableButtons(self, dumCmd=None):
        """Enable or disable widgets, as appropriate."""

        isRunning = self.isRunning
        self.shutterWdg.setEnable(not isRunning)
        self.cancelBtn.setEnable(isRunning)

    def updateStatus(self, keyVar=None):
        """Shutter position keyword callback."""

        keyVar = self.model.shutter_position
        isCurrent = keyVar.isCurrent

        with self.updateLock():
            if keyVar[0] == '?' or isCurrent is False:
                self.shutterWdg['offvalue'] = "?"
                self.shutterWdg.set("?", isCurrent=False)
                return

            if keyVar[0] == 'open':
                self.shutterWdg.setDefault(True)
                self.shutterWdg.set(True, isCurrent=isCurrent)
            elif keyVar[0] == 'closed':
                self.shutterWdg['offvalue'] = "Closed"
                self.shutterWdg.setDefault(False)
                self.shutterWdg.set(False, isCurrent=isCurrent)
            else:
                self.shutterWdg.setIsCurrent(False)
