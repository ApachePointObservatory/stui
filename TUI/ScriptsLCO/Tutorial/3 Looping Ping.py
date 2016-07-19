class ScriptClass(object):
    """Tutorial script to test the aliveness of several actors.
    
    This version uses a loop.
    """
    def __init__(self, sr):
        pass

    def run(self, sr):
        for actorCmd in (
            "alerts ping",
            "boss ping",
            "gcamera ping",
            "guider ping",
            "mcp ping",
            "platedb ping",
            "sop ping",
            "tcc show time",
        ):
            actor, cmdStr = actorCmd.split(None, 1)
            yield sr.waitCmd(
                actor = actor,
                cmdStr = cmdStr,
            )
