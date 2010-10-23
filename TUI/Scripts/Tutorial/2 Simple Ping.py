class ScriptClass(object):
    """Ping two actors"""
    def __init__(self, sr):
        pass

    def run(self, sr):
        yield sr.waitCmd(
            actor = "alerts",
            cmdStr = "ping",
        )
        yield sr.waitCmd(
            actor = "boss",
            cmdStr = "ping",
        )
