#  06/09/2010 EM, added check of fail for guider cartridge
#  05/16/2011 resizable window, added three apogee actors 

import RO.Wdg
import TUI.Models
from datetime import datetime

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode (which doesn't DO anything)
        # if False, real time run
        sr.debug = False
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=30, height =33,)
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.redWarn=RO.Constants.sevError
    
    def run(self, sr):
        print "   "
        utc_datetime = datetime.utcnow()
        tm=utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
        print 'testActors, %s ' % (tm)
        self.logWdg.addMsg('testActors,  %s  ' % (tm))

  #      print "----- start TestActors.py ----- "
  #      print "     "+str(datetime.utcnow())
  #      self.logWdg.addMsg("---TestActors ---" )
  #      self.logWdg.addMsg("     "+str(datetime.utcnow()))   
        self.logWdg.addMsg(" ")  
        for actorCmd in [
            "alerts ping",
            "alerts status",
    #        "apo ping",            
    #        "apo status",
            "apogee status",
            "apogeecal status",
            "apogeeql status",            
            "boss ping",
            "boss status",
            "gcamera ping",
            "gcamera status",
            "ecamera ping",
            "ecamera status",
            "guider ping",
            "guider status",
            "hub status",
            "mcp ping",
            "msg just testing",
            "perms status",
            "platedb ping",
            "platedb status",
            "sop ping",
            "sop status",
            "sos ping",
            "tcc show status",
            "tcc show time",
            "keys getFor=hub version",
     #       "test to fail",
        ]:
            actor, cmd = actorCmd.split(None, 1)
            yield sr.waitCmd(
                actor=actor,
                cmdStr=cmd,
                checkFail = False,
            )
            cmdVar = sr.value
            if cmdVar.didFail:
                print actorCmd, "--- * FAILED *"
                self.logWdg.addMsg("%s ** FAILED **" % (actorCmd),severity=RO.Constants.sevError)
            else:
                print actorCmd, "--- ok!"
                self.logWdg.addMsg("%s OK" % (actorCmd,))

        self.logWdg.addMsg("--------" ) 
