#!/usr/bin/env python
# encoding: utf-8
#
# @Author: José Sánchez-Gallego
# @Date: Jan 25, 2018
# @Filename: ScriptWdg.py


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import contextlib
import Tkinter

import opscore.actor
import RO.Wdg

import TUI.Models

from .CommandWdgSet import CommandWdgSet


__all__ = ['ScriptWdg']


# A list of script that is safe to run. Scripts not in this list will be shown in red.
SAFE_SCRIPTS = ['cartchange']


class ScriptWdg(CommandWdgSet):
    """Widget for SOP scripts."""

    def __init__(self, master, msgBar, statusBar, helpURL=None):

        self.msgBar = msgBar
        self.statusBar = statusBar
        self.helpURL = helpURL

        super(ScriptWdg, self).__init__('script', dispName='Run Script', parameterList=(),
                                        realStageStr='', fakeStageStr='', actor='sop',
                                        canAbort=True, abortCmdStr='stopScript')

        self.build(master=master,
                   msgBar=self.msgBar,
                   statusBar=self.statusBar,
                   helpURL=self.helpURL,
                   startColCommandFrame=1)  # Starts in col 1 so that we can add
                                            # the dropdown menu in col 0.

        self.scriptNameWdg = RO.Wdg.OptionMenu(master=self.commandFrame,
                                               callFunc=self._script_selected,
                                               items=[], helpText='Script to run')
        self.scriptNameWdg.grid(row=0, column=0)

        sopModel = TUI.Models.getModel('sop')
        sopModel.availableScripts.addCallback(self._availableScriptsCallback)

    def enableWdg(self, dumWdg=None):
        """Enables/disables the different widgets depending on the command state."""

        # Need to check if scriptNameWdg exists because this method is called
        # when build() is called and at that time scriptNameWdg has not been created.
        if hasattr(self, 'scriptNameWdg'):
            self.scriptNameWdg.setEnable(self.isDone or self.state is None)

        # For some reason super'n enableWdg here doesn't work completely so
        # we just enable start, stop, and abort accordingly.

        self.startBtn.setEnable(self.isDone or self.state is None)
        self.stopBtn.setEnable(self.isRunning)
        self.abortBtn.setEnable(len(self.currCmdInfoList) > 0)

    def getCmdStr(self):
        """Returns the command string for the current settings."""

        return 'runScript scriptName={}'.format(self.scriptNameWdg.getString())

    def _availableScriptsCallback(self, availableScripts):
        """Listens to ``availableScripts`` and populates the dropdown menu."""

        if availableScripts[0] is None:
            self.scriptNameWdg.setItems([], checkDef=True)
        else:
            items = sorted(availableScripts[0].split(','))
            if len(items) > 0:
                self.scriptNameWdg.setItems(items, checkDef=True)
                self.scriptNameWdg['width'] = max([len(script) for script in items])
                if self.scriptNameWdg.defValue is None:
                    self.scriptNameWdg.defValue = items[0]
                    self.scriptNameWdg.restoreDefault()

            for index in range(self.scriptNameWdg._menu.index('end') + 1):
                label = self.scriptNameWdg._menu.entrycget(index, 'label')
                colour = 'black' if label.lower() in SAFE_SCRIPTS else 'red'
                self.scriptNameWdg._menu.entryconfig(index, foreground=colour)

    def _script_selected(self, wdg):
        """Changes the colour of the selected element in the widget."""

        if wdg.getString() is not None and wdg.getString().lower() in SAFE_SCRIPTS:
            wdg.config(fg='black', activeforeground='black', highlightcolor='black')
        else:
            wdg.config(fg='red', activeforeground='red', highlightcolor='red')

    def _commandStateCallback(self, keyVar):
        """Command state callback.

        SOP does not output ``scriptState`` on init, so if the cmdState is not
        defined we just clear the label.

        """

        cmdState = keyVar[3]

        if cmdState is None:
            self.setState(state=None, isCurrent=True)
        else:
            if cmdState == 'stopped':  # CommandWdgSet does not understand stopped so replaces it.
                cmdState = 'aborted'
            self.setState(state=cmdState, isCurrent=keyVar.isCurrent)


if __name__ == '__main__':

    import TUI.Base.Wdg
    import TestData

    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    root.resizable(width=0, height=0)

    statusBar = TUI.Base.Wdg.StatusBar(master=root, playCmdSounds=True)

    testFrame = ScriptWdg(master=root, statusBar=statusBar)
    testFrame.pack(side='top')
    statusBar.pack(side='top', expand=True, fill="x")

    Tkinter.Button(root, text='Demo', command=TestData.animate).pack(side='top')

    TestData.start()

    tuiModel.reactor.run()
