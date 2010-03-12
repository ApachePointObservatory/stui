import RO.Wdg
import TUI.Models

class ScriptClass(object):
    """Tutorial script to print the version of some actors
    """
    def __init__(self, sr):
        self.bossModel = TUI.Models.getModel("boss")
        self.gcameraModel = TUI.Models.getModel("gcamera")
        self.guiderModel = TUI.Models.getModel("guider")
        self.tccModel = TUI.Models.getModel("tcc")
        
        self.actorKeyVarList = (
            ("boss", self.bossModel.version),
            ("gcamera", self.gcameraModel.version),
            ("guider", self.guiderModel.version),
        )
        
        self.logWdg = RO.Wdg.LogWdg(
            master = sr.master,
            width = 40,
            height = len(self.actorKeyVarList) + 2, # avoids scrolling
        )
        self.logWdg.grid(row=0, column=0, sticky="news")
        
    def run(self, sr):
        for actor, keyVar in self.actorKeyVarList:
            versionStr = sr.getKeyVar(keyVar, ind=0, defVal="?")
            self.logWdg.addMsg("%s\t%s" % (actor, versionStr))

        yield sr.waitCmd(actor="tcc", cmdStr="show version", keyVars=[self.tccModel.text])
        tccVers = sr.value.getLastKeyVarData(self.tccModel.text)[0]
        self.logWdg.addMsg("%s\t%s" % ("tcc", tccVers))
