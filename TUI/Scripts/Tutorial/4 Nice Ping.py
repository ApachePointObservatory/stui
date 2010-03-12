import RO.Constants

class ScriptClass(object):
    """Tutorial script to test the aliveness of various actors.

    This is the recommended version. Unlike 3 Looping Ping:
    - It outputs the results to a log window
    - It uses checkFail=False to continue and check all actors even if one command fails.
    """
    def __init__(self, sr):
        """Display the exposure status panel.
        """
        # if True, run in debug-only mode (which doesn't send anything to the hub, it just pretends)
        sr.debug = False
        
        # Set the command list here so we can set the height of the log window
        # to match the number of commands, to avoid the need to scroll.
        # If you have so many commands that the window gets too tall then use a fixed height (e.g. 20)
        # and let it scroll, or consider ways to present the output using less text.
        self.actorCmdList = (
            "alerts ping",
            "boss ping",
            "gcamera ping",
            "guider ping",
            "mcp ping",
            "platedb ping",
            "sop ping",
            "tcc show time",
        )
        
        # log window to display the results of each command
        self.logWdg = RO.Wdg.LogWdg(
            master = sr.master,
            width = 30,
            height = len(self.actorCmdList) + 1, # avoids scrolling
        )
        self.logWdg.grid(row=0, column=0, sticky="news")
    
    def run(self, sr):
        """Run the script"""
        for actorCmd in self.actorCmdList:
            # actorCmd.split(None, 1) divides the string into two strings at the first whitespace:
            # None means any whitespace (spaces and/or tabs); " " would work just as well in this case
            # 1 means just split once; if omitted it would split at every occurrence of whitespace
            # which would fail on "tcc show time" because it would return three strings,
            # but actor, cmdStr = demands exactly two
            actor, cmdStr = actorCmd.split(None, 1)
            yield sr.waitCmd(
                actor = actor,
                cmdStr = cmdStr,
                checkFail = False,
            )
            cmdVar = sr.value
            if cmdVar.didFail:
                self.logWdg.addMsg("%s FAILED" % (actor,), severity=RO.Constants.sevError)
            else:
                self.logWdg.addMsg("%s OK" % (actor,))
