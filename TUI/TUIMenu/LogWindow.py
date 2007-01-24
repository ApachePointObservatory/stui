#!/usr/bin/env python
"""Specialized version of RO.Wdg.LogWdg that adds nice filtering
and text highlighting.

To do:
- Use tcl to check regular expressions (instead of re.compile)
  because tcl applies them. At least in most cases
  (python applies Actors regular expressions).

History:
History:
2003-12-17 ROwen    Added addWindow and renamed to UsersWindow.py.
2004-05-18 ROwen    Stopped obtaining TUI model in addWindow; it was ignored.
2004-06-22 ROwen    Modified for RO.Keyvariable.KeyCommand->CmdVar
2004-07-22 ROwen    Play sound queue when user command finishes.
                    Warn (message and sound queue) if user command has no actor.
2004-08-25 ROwen    Do not leave command around if user command has no actor. It was confusing.
2004-09-14 ROwen    Minor change to make pychecker happier.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2006-03-10 ROwen    Modified to prepend UTC time to each logged message.
                    Modified to reject multi-line commands.
2006-03-16 ROwen    Modified to accept a command that ends with "\n".
2006-10-25 ROwen    Totally rewritten to use overhauled RO.Wdg.LogWdg.
2006-10-27 ROwen    Filtering and highlighting now show helpful messages in the status bar.
                    Changed the default severity from Warnings to Normal.
                    Regular expressions are checked and an error message shown if invalid.
                    Actors entries are checked and an error message shown if any don't match.
                    Fixed actor highlighting to remove old highlight.
2006-11-02 ROwen    Modified to filter by default.
2006-11-06 ROwen    Fixed filtering and highlighting to more reliably unfilter or unhighlight
                    for invalid inputs.
                    Fixed selections to show over highlighted text.
                    Added Prev and Next highlight buttons.
                    Clear "Removing highlight" message from status bar at instantiation.
"""
import re
import time
import Tkinter
try:
    set
except NameError:
    from sets import Set as set
import RO.Alg
import RO.TkUtil
import RO.Wdg
import TUI.HubModel
import TUI.TUIModel
import TUI.PlaySound

HelpURL = "TUIMenu/LogWin.html"

def addWindow(tlSet):
    tlSet.createToplevel(
        name = "TUI.Log",
        defGeom = "603x413+430+280",
        resizable = True,
        visible = False,
        wdgFunc = TUILogWdg,
    )

FilterMenuPrefix = "+ "
HighlightLineColor = "#bdffe0"
HighlightColorScale = 0.92
HighlightTag = "highlighttag"
HighlightTextTag = "highlighttexttag"
ShowTag = "showtag"

SevTagDict = {
    RO.Constants.sevDebug: "sev_debug",
    RO.Constants.sevNormal: "sev_normal",
    RO.Constants.sevWarning: "sev_warning",
    RO.Constants.sevError: "sev_error",
}
SevTags = ("sev_debug", "sev_normal", "sev_warning", "sev_error")
SevMenuTagsDict = dict(
    debug = SevTags,
    normal = SevTags[1:],
    warnings = SevTags[2:],
    errors = SevTags[3:],
    none = [],
)

ActorTagPrefix = "act_"
CmdrTagPrefix = "cmdr_"

class RegExpInfo(object):
    """Object holding a regular expression
    and associated tags.
    
    Checks the regular expression and raises RuntimeError if invalid.
    """
    def __init__(self, regExp, tag, lineTag):
        self.regExp = regExp
        self.tag = tag
        self.lineTag = lineTag
        try:
            re.compile(regExp)
        except re.error:
            raise RuntimeError("invalid regular expression %r" % (regExp,))
    
    def __str__(self):
        return "RegExpInfo(regExp=%r, tag=%r, lineTag=%r)" % \
            (self.regExp, self.tag, self.lineTag)

class TUILogWdg(Tkinter.Frame):
    def __init__(self,
        master,
        maxCmds = 50,
        maxLines = 5000,
    **kargs):
        """
        Inputs:
        - master: master widget
        - maxCmds: maximun # of commands
        - maxLines: the max number of lines to display, ignoring wrapping
        - height: height of text area, in lines
        - width: width of text area, in characters
        - **kargs: additional keyword arguments for Frame
        """
        Tkinter.Frame.__init__(self, master, **kargs)

        tuiModel = TUI.TUIModel.getModel()
        tuiModel.dispatcher.setLogFunc(self.logMsg)
        self.dispatcher = tuiModel.dispatcher
        self.filterRegExpInfo = None
        self.highlightRegExpInfo = None
        self.highlightTag = None
        
        row = 0
        
        self.ctrlFrame1 = Tkinter.Frame(self)
        ctrlCol1 = 0

        # Filter controls
        
        self.filterOnOffWdg = RO.Wdg.Checkbutton(
            self.ctrlFrame1,
            text = "Filter:",
            defValue = True,
            callFunc = self.doFilterOnOff,
            helpText = "enable or disable filtering",
            helpURL = HelpURL,
            indicatoron = False,
        )
        self.filterOnOffWdg.grid(row=0, column=ctrlCol1)
        ctrlCol1 += 1

        self.filterFrame = Tkinter.Frame(self.ctrlFrame1)
        
        filtCol = 0

        self.severityMenu = RO.Wdg.OptionMenu(
            self.filterFrame,
            items = ("Debug", "Normal", "Warnings", "Errors", "None"),
            defValue = "Normal",
            callFunc = self.applyFilter,
            helpText = "show replies with at least this severity",
            helpURL = HelpURL,
        )
        self.severityMenu.grid(row=0, column=filtCol)
        filtCol += 1
    
#       RO.Wdg.StrLabel(self.filterFrame, text="and").grid(row=0, column=filtCol)
#       filtCol += 1
        
        self.filterCats = ("Actor", "Actors", "Commands", "Text")
        filterItems = [""] + [FilterMenuPrefix + fc for fc in self.filterCats]
        self.filterMenu = RO.Wdg.OptionMenu(
            self.filterFrame,
            items = filterItems,
            defValue = "",
            callFunc = self.doFilter,
            helpText = "additional messages to show",
            helpURL = HelpURL,
        )
        self.filterMenu.grid(row=0, column=filtCol)
        filtCol += 1
        
        # grid all category-specific widgets in the same place
        # (but then show one at a time based on filterMenu)
        self.filterActorWdg = RO.Wdg.OptionMenu(
            self.filterFrame,
            items = ("",),
            defValue = "",
            callFunc = self.doFilterActor,
            helpText = "show commands and replies for this actor",
            helpURL = HelpURL,
        )
        self.filterActorWdg.grid(row=0, column=filtCol)
        
        self.filterActorsWdg = RO.Wdg.StrEntry(
            self.filterFrame,
            width = 20,
            doneFunc = self.doFilterActors,
            helpText = "space-separated actors to show; . = any char; * = any chars",
            helpURL = HelpURL,
        )       
        self.filterActorsWdg.grid(row=0, column=filtCol)
    
        self.filterCommandsWdg = RO.Wdg.StrEntry(
            self.filterFrame,
            width = 15,
            doneFunc = self.doFilterCommands,
            helpText = "space-separated command numbers to show; . = any char; * = any chars",
            helpURL = HelpURL,
        )       
        self.filterCommandsWdg.grid(row=0, column=filtCol)
        
        self.filterTextWdg = RO.Wdg.StrEntry(
            self.filterFrame,
            width = 15,
            doneFunc = self.doFilterText,
            helpText = "text (regular expression) to show",
            helpURL = HelpURL,
        )       
        self.filterTextWdg.grid(row=0, column=filtCol)
        
        # all filter controls that share a column have been gridded
        filtCol += 1
        
        self.filterFrame.grid(row=0, column=ctrlCol1)
        ctrlCol1 += 1

        # Find controls (and separator)
        
        # Note: controls are gridded instead of packed
        # so they can easily be hidden and shown
        # (there is no pack_remove command).
        
        #expandFrame = Tkinter.Frame(self).grid(row=0, column=ctrlCol1)
        self.ctrlFrame1.grid_columnconfigure(ctrlCol1, weight=1)
        ctrlCol1 += 1
        
        self.findButton = RO.Wdg.Button(
            master = self.ctrlFrame1,
            text = "Find:",
            command = self.doSearchBackwards,
            helpText = "press or type <return> to search backwards; type <ctrl-return> to search forwards",
            helpURL = HelpURL,
        )
        self.findButton.grid(row=0, column=ctrlCol1)
        ctrlCol1 += 1
        
        self.findEntry = RO.Wdg.StrEntry(
            master = self.ctrlFrame1,
            width = 15,
            helpText = "search regular expression; <return> to search backwards, <ctrl-return> forwards",
            helpURL = HelpURL,
        )
        self.findEntry.bind('<KeyPress-Return>', self.doSearchBackwards)
        self.findEntry.bind('<Control-Return>', self.doSearchForwards)
        self.findEntry.grid(row=0, column=ctrlCol1)
    
        self.ctrlFrame1.grid(row=row, column=0, sticky="ew")
        row += 1
        
        self.ctrlFrame2 = Tkinter.Frame(self)
        ctrlCol2 = 0

        self.highlightOnOffWdg = RO.Wdg.Checkbutton(
            self.ctrlFrame2,
            text = "Highlight:",
            indicatoron = False,
            callFunc = self.doShowHideAdvanced,
            helpText = "enable or disable highlighting",
            helpURL = HelpURL,
        )
        self.highlightOnOffWdg.grid(row=0, column=ctrlCol2)
        ctrlCol2 += 1

        self.highlightFrame = Tkinter.Frame(self.ctrlFrame2)
        highlightCol = 0
        
        self.highlightCats = ("Actor", "Actors", "Commands", "Text")
        
        self.highlightMenu = RO.Wdg.OptionMenu(
            self.highlightFrame,
            items = self.highlightCats,
            defValue = "Text",
            callFunc = self.doHighlight,
            helpText = "show actor or command",
            helpURL = HelpURL,
        )
        self.highlightMenu.grid(row=0, column=highlightCol)
        highlightCol += 1
        
        # grid all category-specific widgets in the same place
        # (but then show one at a time based on highlightMenu)
        self.highlightActorWdg = RO.Wdg.OptionMenu(
            self.highlightFrame,
            items = ("",),
            defValue = "",
            callFunc = self.doHighlightActor,
            helpText = "highlight commands and replies for this actor",
            helpURL = HelpURL,
        )
        self.highlightActorWdg.grid(row=0, column=highlightCol)
        
        self.highlightActorsWdg = RO.Wdg.StrEntry(
            self.highlightFrame,
            width = 20,
            doneFunc = self.doHighlightActors,
            helpText = "space-separated actors to highlight; . = any char; * = any chars",
            helpURL = HelpURL,
        )       
        self.highlightActorsWdg.grid(row=0, column=highlightCol)
    
        self.highlightCommandsWdg = RO.Wdg.StrEntry(
            self.highlightFrame,
            width = 15,
            doneFunc = self.doHighlightCommands,
            helpText = "space-separated command numbers to highlight; . = any char; * = any chars",
            helpURL = HelpURL,
        )       
        self.highlightCommandsWdg.grid(row=0, column=highlightCol)

        self.highlightTextWdg = RO.Wdg.StrEntry(
            self.highlightFrame,
            width = 20,
            doneFunc = self.doHighlightText,
            helpText = "text to highlight; regular expression",
            helpURL = HelpURL,
        )       
        self.highlightTextWdg.grid(row=0, column=highlightCol)
        
        # all highlight widgets that share a column have been gridded
        highlightCol += 1
        
        self.highlightPlaySoundWdg = RO.Wdg.Checkbutton(
            self.highlightFrame,
            text = "Play Sound",
            indicatoron = True,
            helpText = "play a sound when new highlighted text is received?",
            helpURL = HelpURL,
        )
        self.highlightPlaySoundWdg.grid(row=0, column=highlightCol)
        highlightCol += 1
        
        self.prevHighlightWdg = RO.Wdg.Button(
            self.highlightFrame,
            text = u"\N{BLACK UP-POINTING TRIANGLE}", # "Prev",
            callFunc = self.doShowPrevHighlight,
            helpText = "show previous highlighted text",
            helpURL = HelpURL,
        )
        self.prevHighlightWdg.grid(row=0, column=highlightCol)
        highlightCol += 1
        
        self.nextHighlightWdg = RO.Wdg.Button(
            self.highlightFrame,
            text = u"\N{BLACK DOWN-POINTING TRIANGLE}", # "Next",
            callFunc = self.doShowNextHighlight,
            helpText = "show next highlighted text",
            helpURL = HelpURL,
        )
        self.nextHighlightWdg.grid(row=0, column=highlightCol)
        highlightCol += 1
    
        self.highlightFrame.grid(row=0, column=ctrlCol2, sticky="w")
        ctrlCol2 += 1
        
        self.ctrlFrame2.grid(row=row, column=0, sticky="w")
        row += 1
        
        self.logWdg = RO.Wdg.LogWdg(
            self,
            maxLines = maxLines,
            helpURL = HelpURL,
        )
        self.logWdg.grid(row=row, column=0, sticky="nwes")
        self.grid_rowconfigure(row, weight=1)
        self.grid_columnconfigure(0, weight=1)
        row += 1
        
        self.statusBar = RO.Wdg.StatusBar(self, helpURL=HelpURL)
        self.statusBar.grid(row=row, column=0, sticky="ew")
        row += 1

        cmdFrame = Tkinter.Frame(self)
                
        RO.Wdg.StrLabel(
            cmdFrame,
            text = "Command:"
        ).pack(side="left")

        self.defActorWdg = RO.Wdg.OptionMenu(
            cmdFrame,
            items = ("", "hub", "tcc", "gcam"),
            defValue = "",
            callFunc = self.doDefActor,
            helpText = "default actor for new commands",
            helpURL = HelpURL,
        )
        self.defActorWdg.pack(side="left")
        
        self.cmdWdg = RO.Wdg.CmdWdg(
            cmdFrame,
            maxCmds = maxCmds,
            cmdFunc = self.doCmd,
            helpText = "command to send to hub; <return> to send",
            helpURL = HelpURL,
        )
        self.cmdWdg.pack(side="left", expand=True, fill="x")
        
        cmdFrame.grid(row=5, column=0, columnspan=5, sticky="ew")
        
        hubModel = TUI.HubModel.getModel()
        hubModel.actors.addCallback(self.updActors)
        
        # set up severity tags and tie them to color preferences
        self._severityPrefDict = RO.Wdg.WdgPrefs.getSevPrefDict()
        for sev, pref in self._severityPrefDict.iteritems():
            sevTag = SevTagDict[sev]
            if sev == RO.Constants.sevNormal:
                # normal color is already automatically updated
                # but do make tag known to text widget
                self.logWdg.text.tag_configure(sevTag)
                continue
            pref.addCallback(RO.Alg.GenericCallback(self._updSevTagColor, sevTag), callNow=True)
        
        self.actorDict = {}
    
        # set up and configure other tags
        hcPref = tuiModel.prefs.getPrefVar("Highlight Background")
        if hcPref:
            hcPref.addCallback(self.updHighlightColor, callNow=True)
        else:
            self.updHighlightColor(HighlightLineColor)
        self.logWdg.text.tag_configure(ShowTag, elide=False)
        self.logWdg.text.tag_raise("sel")
        
        self.doFilterOnOff()
        self.doShowHideAdvanced()
        self.logWdg.text.bind('<KeyPress-Return>', RO.TkUtil.EvtNoProp(self.doSearchBackwards))
        self.logWdg.text.bind('<Control-Return>', RO.TkUtil.EvtNoProp(self.doSearchForwards))
        
        # clear "Removing highlight" message from status bar
        self.statusBar.clear()

    def doShowNextHighlight(self, wdg=None):
        self.logWdg.findTag(HighlightTag, backwards=False, doWrap=False)
        
    def doShowPrevHighlight(self, wdg=None):
        self.logWdg.findTag(HighlightTag, backwards=True, doWrap=False)
        
    def addOutput(self, msgStr, tags=()):
        """Log a message, prepending the current time.
        """
        # use this if fractional seconds wanted
#       timeStr = datetime.datetime.utcnow().time().isoformat()[0:10]
        # use this if integer seconds OK
        timeStr = time.strftime("%H:%M:%S", time.gmtime())
        outStr = " ".join((timeStr, msgStr))
        #print "addOutput(%r, %r)" % (outStr, tags)
        self.logWdg.addOutput(outStr, tags)
        if self.filterRegExpInfo or self.highlightRegExpInfo:
            if self.filterRegExpInfo:
                self.findRegExp(
                    self.filterRegExpInfo,
                    removeTags = False,
                    elide = True,
                    startInd = "end - 2 lines",
                )
            if self.highlightRegExpInfo:
                nFound = self.findRegExp(
                    self.highlightRegExpInfo,
                    removeTags = False,
                    startInd = "end - 2 lines",
                )
                if nFound > 0 and self.highlightPlaySoundWdg.getBool():
                    TUI.PlaySound.logHighlightedText()

    def applyFilter(self, wdg=None):
        """Apply current filter settings.
        """
        self.filterRegExpInfo = None
        filterEnabled = self.filterOnOffWdg.getBool()
        filterCat = self.filterMenu.getString()
        filterCat = filterCat[len(FilterMenuPrefix):] # strip prefix
        #print "applyFilter: filterEnabled=%r; filterCat=%r" % (filterEnabled, filterCat)

        if not filterEnabled:
            self.logWdg.showAllText()
            self.statusBar.setMsg(
                "Showing all messages",
                isTemp = True,
            )
            return

        if filterCat:
            func = getattr(self, "doFilter%s" % (filterCat,))
            func()
        else:
            # just filter on severity
            self.showSeverityOnly()
    
    def clearHighlight(self, showMsg=True):
        """Remove all highlighting"""
        if showMsg:
            self.statusBar.setMsg(
                "Removing highlight",
                isTemp = True,
            )
        self.logWdg.text.tag_remove(HighlightTag, "0.0", "end")
        self.logWdg.text.tag_remove(HighlightTextTag, "0.0", "end")
        
    def dispatchCmd(self, actorCmdStr):
        """Executes a command (if a dispatcher was specified).

        Inputs:
        - actorCmdStr: a string containing the actor
            and command, separated by white space.
            
        On error, logs a message (does not raise an exception).
        
        Implementation note: the command is logged by the dispatcher
        when it is dispatched.
        """
        actor = "TUI"
        try:
            actorCmdStr = actorCmdStr.strip()
    
            if "\n" in actorCmdStr:
                raise RuntimeError("Cannot execute multiple lines; use Run_Command script instead.")
    
            try:
                actor, cmdStr = actorCmdStr.split(None, 1)
            except ValueError:
                raise RuntimeError("Cannot execute %r; no command found." % (actorCmdStr,))
    
            # issue the command
            RO.KeyVariable.CmdVar (
                actor = actor,
                cmdStr = cmdStr,
                callFunc = self._cmdCallback,
                dispatcher = self.dispatcher,
            )
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            self.logMsg("Text=%r" % (str(e),), severity=RO.Constants.sevError, actor=actor)
            TUI.PlaySound.cmdFailed()

    def compileRegExp(self, regExp, flags):
        """Attempt to compile the regular expression.
        Show error in status bar and return None if it fails.
        """
        try:
            return re.compile(regExp, flags)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.statusBar.setMsg(
                "%r is not a valid regular expression" % (regExp,),
                severity = RO.Constants.sevError,
                isTemp = True,
            )
        return None

    def doCmd(self, cmdStr):
        """Handle commands typed into the command bar.
        Note that dispatching the command automatically logs it.
        """
        self.dispatchCmd(cmdStr)
        self.logWdg.text.see("end")
        
        defActor = self.defActorWdg.getString()
        if not defActor:
            return
        self.cmdWdg.set(defActor + " ")
        self.cmdWdg.icursor("end")
    
    def doSearchBackwards(self, evt=None):
        """Search backwards for search string"""
        searchStr = self.findEntry.get()
        self.logWdg.search(searchStr, backwards=True, noCase=True, regExp=True)
    
    def doSearchForwards(self, evt=None):
        """Search backwards for search string"""
        searchStr = self.findEntry.get()
        self.logWdg.search(searchStr, backwards=False, noCase=True, regExp=True)
    
    def doShowHideAdvanced(self, wdg=None):
        if self.highlightOnOffWdg.getBool():
            self.highlightFrame.grid()
            self.doHighlight()
        else:
            self.highlightFrame.grid_remove()
            self.doHighlight()
            
    def doFilterOnOff(self, wdg=None):
        doFilter = self.filterOnOffWdg.getBool()
        if doFilter:
            self.filterFrame.grid()
        else:
            self.filterFrame.grid_remove()
        self.doFilter()

    def doDefActor(self, wdg=None):
        """Handle default actor menu."""
        defActor = self.defActorWdg.getString()
        if defActor:
            defActor += " "

        actorCmd = self.cmdWdg.get()
        if not actorCmd:
            self.cmdWdg.set(defActor)
        else:
            actorCmdList = actorCmd.split(None, 1)
            if len(actorCmdList) > 1:
                self.bell()
            else:
                self.cmdWdg.set(defActor)
        
        self.cmdWdg.icursor("end")
        self.cmdWdg.focus_set()
    
    def doFilter(self, wdg=None):
        """Show appropriate highlight widgets and apply appropriate function
        """
        filterCat = self.filterMenu.getString()
        filterCat = filterCat[len(FilterMenuPrefix):] # strip prefix
        #print "doFilter; cat=%r" % (filterCat,)
        
        for cat in self.filterCats:
            wdg = getattr(self, "filter%sWdg" % (cat,))
            if cat == filterCat:
                wdg.grid()
            else:
                wdg.grid_remove()
        
        self.applyFilter()
    
    def doFilterActor(self, wdg=None):
        self.showSeverityOnly()
        actor = self.filterActorWdg.getString().lower()
        if not actor:
            return
        self.showSeverityAndActors([actor])
    
    def doFilterActors(self, wdg=None):
        self.showSeverityOnly()
        regExpList = self.filterActorsWdg.getString().split()
        if not regExpList:
            return
        try:
            actors = self.getActors(regExpList)
        except RuntimeError, e:
            self.statusBar.setMsg(str(e), severity = RO.Constants.sevError, isTemp = True)
            TUI.PlaySound.cmdFailed()
            return
            
        self.showSeverityAndActors(actors)
    
    def doFilterCommands(self, wdg=None):
        self.showSeverityOnly()
        cmds = self.filterCommandsWdg.getString().split()
        if not cmds:
            return
        
        # create regular expression
        # it must include my username so only my commands are shown
        # it must show both outgoing commands: UTCDate username cmdNum
        # and replies: UTCDate cmdNum
        orCmds = "|".join(["(%s)" % (cmd,) for cmd in cmds])
        
        cmdr = self.dispatcher.connection.getCmdr()
        
        regExp = r"^\d\d:\d\d:\d\d( +%s)? +(%s) " % (cmdr, orCmds)
        try:
            regExpInfo = RegExpInfo(regExp, None, ShowTag)
        except RuntimeError:
            self.showSeverityOnly()
            self.statusBar.setMsg(
                "Invalid command list %s" % (" ".join(cmds)),
                severity = RO.Constants.sevError,
                isTemp = True,
            )
            TUI.PlaySound.cmdFailed()
            return
        
        sev = self.severityMenu.getString().lower()
        if len(cmds) == 1:
            self.statusBar.setMsg(
                "Showing %s and commands %s" % (sev, cmds[0]),
                isTemp = True,
            )
        else:
            self.statusBar.setMsg(
                "Showing %s and commands %s" % (sev, " ".join(cmds)),
                isTemp = True,
            )
        self.filterRegExpInfo = regExpInfo
        self.findRegExp(self.filterRegExpInfo, elide=True)
        self.showSeverityAndTags([ShowTag])
    
    def doFilterText(self, wdg=None):
        self.showSeverityOnly()
        regExp = self.filterTextWdg.getString()
        if not regExp:
            return
            
        try:
            regExpInfo = RegExpInfo(regExp, None, ShowTag)
        except RuntimeError:
            self.statusBar.setMsg(
                "Invalid regular expression %r" % (regExp,),
                severity = RO.Constants.sevError,
                isTemp = True,
            )
            TUI.PlaySound.cmdFailed()
            return
        
        sev = self.severityMenu.getString().lower()
        self.statusBar.setMsg(
            "Showing %s and text %r" % (sev, regExp),
            isTemp = True,
        )
        self.filterRegExpInfo = regExpInfo
        self.findRegExp(self.filterRegExpInfo, elide=True)
        self.showSeverityAndTags([ShowTag])

    def doHighlight(self, wdg=None):
        """Show appropriate highlight widgets and apply appropriate function
        """
        self.highlightRegExpInfo = None
        highlightCat = self.highlightMenu.getString()
        highlightEnabled = self.highlightOnOffWdg.getBool()
        #print "doHighlight; cat=%r; enabled=%r" % (highlightCat, highlightEnabled)
        
        for cat in self.highlightCats:
            wdg = getattr(self, "highlight%sWdg" % (cat,))
            if cat == highlightCat:
                wdg.grid()
            else:
                wdg.grid_remove()

        # apply highlighting
        if highlightEnabled and highlightCat:
            func = getattr(self, "doHighlight%s" % (highlightCat,))
            func()
        else:
            self.clearHighlight()
        
    def doHighlightActor(self, wdg=None):
        self.clearHighlight()
        actor = self.highlightActorWdg.getString().lower()
        if not actor:
            return
        self.highlightActors([actor])
    
    def doHighlightActors(self, wdg=None):
        self.clearHighlight()
        regExpList = self.highlightActorsWdg.getString().split()
        if not regExpList:
            return
        try:
            actors = self.getActors(regExpList)
        except RuntimeError, e:
            self.statusBar.setMsg(str(e), severity = RO.Constants.sevError, isTemp = True)
            TUI.PlaySound.cmdFailed()
            return
        if not actors:
            return
        self.highlightActors(actors)
    
    def doHighlightCommands(self, wdg=None):
        self.clearHighlight()
        cmds = self.highlightCommandsWdg.getString().split()
        if not cmds:
            return
        
        # create regular expression
        # it must include my username so only my commands are shown
        # it must show both outgoing commands: UTCDate username cmdNum
        # and replies: UTCDate cmdNum
        orCmds = "|".join(["(%s)" % (cmd,) for cmd in cmds])
        
        cmdr = self.dispatcher.connection.getCmdr()
        
        regExp = r"^\d\d:\d\d:\d\d( +%s)? +(%s) " % (cmdr, orCmds)
        try:
            regExpInfo = RegExpInfo(regExp, None, HighlightTag)
        except RuntimeError:
            self.statusBar.setMsg(
                "Invalid command list %s" % (" ".join(cmds)),
                severity = RO.Constants.sevError,
                isTemp = True,
            )
            TUI.PlaySound.cmdFailed()
            return
        
        if len(cmds) == 1:
            self.statusBar.setMsg(
                "Highlighting commands %s" % (cmds[0],),
                isTemp = True,
            )
        else:
            self.statusBar.setMsg(
                "Highlighting commands %s" % (" ".join(cmds),),
                isTemp = True,
            )
        self.highlightRegExpInfo = regExpInfo
        self.findRegExp(self.highlightRegExpInfo, removeTags=False)
    
    def doHighlightText(self, wdg=None):
        self.clearHighlight()
        regExp = self.highlightTextWdg.getString()
        if not regExp:
            return

        try:
            regExpInfo = RegExpInfo(regExp, HighlightTextTag, HighlightTag)
        except RuntimeError:
            self.statusBar.setMsg(
                "Invalid regular expression %r" % (regExp,),
                severity = RO.Constants.sevError,
                isTemp = True,
            )
            TUI.PlaySound.cmdFailed()
            return
        
        self.statusBar.setMsg(
            "Highlighting text %r" % (regExp,),
            isTemp = True,
        )
        self.highlightRegExpInfo = regExpInfo
        self.findRegExp(self.highlightRegExpInfo, removeTags=False)
    
    def findRegExp(self, regExpInfo, removeTags=True, elide=False, startInd="1.0"):
        """Find and tag all lines containing text that matches regExp.
        
        Returns the number of matches.
        
        This is just self.text.findAll with a particular set of options.
        """
        #print "findRegExp(regExpInfo=%r, removeTags=%r, elide=%r, startInd=%r)" % (regExpInfo, removeTags, elide, startInd)
        
        # Warning: you must modify this to call findAll from "after"
        # if this function is called from a variable trace (e.g. an Entry callFunc).
        # Otherwise the count variable is not updated
        # and the routine raises RuntimeError.
        return self.logWdg.findAll(
            searchStr = regExpInfo.regExp,
            tag = regExpInfo.tag,
            lineTag = regExpInfo.lineTag,
            removeTags = removeTags,
            noCase = True,
            regExp = True,
            startInd = startInd,
        )
        
    def getActors(self, regExpList):
        """Return a sorted list of actor
        based on a set of actor name regular expressions.
        
        Raise RuntimeError if any regular expression is invalid or has no match.
        """
        if not regExpList:
            return []

        actors = set()
        compRegExpList = []
        for regExp in regExpList:
            if not regExp.endswith("$"):
                termRegExp = regExp + "$"
            else:
                termRegExp = regExp
            compRegExp = self.compileRegExp(termRegExp, re.IGNORECASE)
            if not compRegExp:
                raise RuntimeError("Invalid regular expression %r" % (regExp,))
            compRegExpList.append((compRegExp, regExp))
            
        badEntries = []
        for (compRegExp, regExp) in compRegExpList:
            foundMatch = False
            for actor in self.actorDict.iterkeys():
                if compRegExp.match(actor):
                    actors.add(actor)
                    foundMatch = True
            if not foundMatch:
                badEntries.append(regExp)
        if badEntries:
            raise RuntimeError("No actors match %s" % (badEntries,))

        #print "getActors(%r) returning %r" % (regExpList, actors)
        actors = list(actors)
        actors.sort()
        return actors

    def getSeverityTags(self):
        """Return a list of severity tags that should be displayed
        based on the current setting of the severity menu.
        """
        sev = self.severityMenu.getString().lower()
        return SevMenuTagsDict[sev]
        
    def highlightActors(self, actors):
        """Highlight text for the specified actors.
        If actors is not empty then a nice message is output.
        
        Warning: does not clear existing highlight.
        """
        if len(actors) == 1:
            self.statusBar.setMsg(
                "Highlighting actor %s" % (actors[0]),
                isTemp = True,
            )
        else:
            self.statusBar.setMsg(
                "Highlighting actors %s" % (" ".join(actors)),
                isTemp = True,
            )
        
        tags = [ActorTagPrefix + actor.lower() for actor in actors]
        for tag in tags:
            tagRanges = self.logWdg.text.tag_ranges(tag)
            if len(tagRanges) > 1:
                self.logWdg.text.tag_add(HighlightTag, *tagRanges)

    def logMsg (self,
        msgStr,
        severity=RO.Constants.sevNormal,
        actor = "TUI",
        cmdr = None,
    ):
        """Writes a message to the log.
        
        Inputs:
        - msgStr: message to display; a final \n is appended
        - severity: message severity (an RO.Constants.sevX constant)
        - actor: name of actor; defaults to TUI
        - cmdr: commander; defaults to self
        """
        # demote normal messages from debug actors to debug severity
        if actor == "cmds" and severity == RO.Constants.sevNormal:
            severity = RO.Constants.sevDebug

        tags = []
        tags.append(SevTagDict.get(severity) or SevTagDict[RO.Constants.sevError])
        if cmdr == None:
            cmdr = self.dispatcher.connection.getCmdr()
        if cmdr:
            tags.append(CmdrTagPrefix + cmdr.lower())
        if actor:
            if actor.startswith("keys."):
                # tag keys.<actor> with the tag for <actor>
                actor = actor[5:]
            tags.append(ActorTagPrefix + actor.lower())
        
        self.addOutput(msgStr + "\n", tags)
    
    def showSeverityAndActors(self, actors):
        """Show all messages of of the appropriate severity
        plus all messages to or from the appropriate actors.
        
        Prints a message to the status bar.
        """
        if not actors:
            self.showSeverityOnly()
            return

        sev = self.severityMenu.getString().lower()

        actorTags = []
        for actor in actors:
            actorTags.append(self.actorDict[actor])
        
        if len(actors) == 1:
            self.statusBar.setMsg(
                "Showing %s and actor %s" % (sev, actors[0]),
                isTemp = True,
            )
        else:
            self.statusBar.setMsg(
                "Showing %s and actors %s" % (sev, " ".join(actors)),
                isTemp = True,
            )
        self.showSeverityAndTags(actorTags)
    
    def showSeverityOnly(self):
        """Show all messages of of the appropriate severity.

        Prints a message to the status bar.
        """
        sev = self.severityMenu.getString().lower()
        if sev == "none":
            self.statusBar.setMsg(
                "Showing no messages!",
                severity = RO.Constants.sevWarning,
                isTemp = True,
            )
        else:
            self.statusBar.setMsg(
                "Showing %s" % (sev,),
                isTemp = True,
            )
        self.logWdg.showTagsOr(self.getSeverityTags())
    
    def showSeverityAndTags(self, tags):
        """Show all messages of of the appropriate severity
        plus all messages tagged with the specified tags.
        """
        #print "showSeverityAndTags(%r)" % (tags,)
        allTags = tuple(tags) + tuple(self.getSeverityTags())
        self.logWdg.showTagsOr(allTags)
    
    def updActors(self, actors, isCurrent, keyVar=None):
        """Actor keyword callback.
        """
        if not actors:
            return
        
        actors = [actor.lower() for actor in actors]
        actors.append("tui")
        actors.sort()
        
        actorTuples = [(actor, "act_" + actor) for actor in actors]
        self.actorDict = dict(actorTuples)
        
        blankAndActors = [""] + actors
        self.defActorWdg.setItems(blankAndActors, isCurrent = isCurrent)
        self.filterActorWdg.setItems(blankAndActors, isCurrent = isCurrent)
        self.highlightActorWdg.setItems(blankAndActors, isCurrent = isCurrent)
    
    def updHighlightColor(self, newColor, colorPrefVar=None):
        """Update highlight color and highlight line color"""

        newTextColor = RO.TkUtil.addColors((newColor, HighlightColorScale))
        self.logWdg.text.tag_configure(HighlightTag, background=newColor)
        self.logWdg.text.tag_configure(HighlightTextTag, background=newTextColor)

    def _updSevTagColor(self, sevTag, color, colorPref):
        """Apply the current color appropriate for the current severity.
        
        Called automatically. Do NOT call manually.
        """
        #print "_updSevTagColor(sevTag=%r, color=%r, colorPref=%r)" % (sevTag, color, colorPref)
        self.logWdg.text.tag_configure(sevTag, foreground=color)
    
    def _cmdCallback(self, msgType, msgDict, cmdVar):
        """Command callback; called when a command finishes.
        """
        if cmdVar.didFail():
            TUI.PlaySound.cmdFailed()
        elif cmdVar.isDone():
            TUI.PlaySound.cmdDone()

    def __del__ (self, *args):
        """Going away; remove myself as the dispatcher's logger.
        """
        self.dispatcher.setLogMsg()
    

if __name__ == '__main__':
    import sys
    import random
    root = RO.Wdg.PythonTk()
    root.geometry("600x350")
    tuiModel = TUI.TUIModel.getModel(testMode = True)
    
    testFrame = TUILogWdg (
        master=root,
        maxLines=50,
    )
    testFrame.grid(row=0, column=0, sticky="nsew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    severities = SevTagDict.keys()
    
    actors = ("ecam", "disExpose","dis", "keys")

    hubModel = TUI.HubModel.getModel()
    hubModel.actors.set(actors)

    for ii in range(10):
        actor = random.choice(actors)
        severity = random.choice((RO.Constants.sevDebug, RO.Constants.sevNormal, \
            RO.Constants.sevWarning, RO.Constants.sevError))
        testFrame.logMsg("%s sample entry %s" % (actor, ii), actor=actor, severity=severity)
    
    root.mainloop()
