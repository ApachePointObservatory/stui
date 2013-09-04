# 06/09/2010  Added defVal variable to check if fail
#   changed format of output from "actor --- ver " to "actor: ver"
# 08/20/2010 changed server name for sdssProcedure
# 05/16/2011  resizable window
# 02/06/2013  refinement
# 08/21/2013  EM: changed script local library name, check is version file exist   
# 08/29/2013  EM: changed script local library name to APO-local


import RO.Wdg
import TUI.Models
import TUI.Version
import httplib
from datetime import datetime
import os

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode 
        # if False, real time run
        sr.debug = False
        self.name="Get Versions"        
        sr.master.winfo_toplevel().wm_resizable(True, True)

        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=30,  height =30,)
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.logWdg.text.tag_config("a", foreground="magenta") 
        self.logWdg.text.tag_config("g", foreground="darkblue") 

        self.redWarn=RO.Constants.sevError
    
    def run(self, sr):
      tm=datetime.utcnow().strftime("%D, %H:%M:%S")

      self.logWdg.addMsg("%s, %s" % (self.name, tm), tags=["a"]) 
      self.logWdg.addMsg("----STUI software: ", tags=["g"])
      self.logWdg.addMsg("STUI: %s   " % (TUI.Version.VersionStr))

      defVal="  FAILED"
  #    tuiModel = TUI.Models.getModel("tui")
  #    conn=tuiModel.getConnection()
  #    if conn:
  #         self.logWdg.addMsg("    STUI is not connected", severity=self.redWarn) 
  #         defVal="  n/a"
           
      alertsModel =TUI.Models.getModel("alerts")
      alv = sr.getKeyVar(alertsModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("alerts: %s   " % (alv,))

      apoModel =TUI.Models.getModel("apo")
      apv = sr.getKeyVar(apoModel.version, ind=0, defVal=defVal)
      if apv == defVal:
          self.logWdg.addMsg("apo:  %s   " % (apv),severity=RO.Constants.sevError)
      else:
          self.logWdg.addMsg("apo:  %s   " % (apv))
  #    yield sr.waitCmd(actor="apo", cmdStr="version",
  #          keyVars=[apoModel.version],checkFail = False,)
  #    cmdVar = sr.value
  #    if cmdVar.didFail:  apv=defVal 
  #    else:   apv = sr.value.getLastKeyVarData(apoModel.version)[0] 
  #    print "apo: "+str(apv)

      bossModel = TUI.Models.getModel("boss")
      bv = sr.getKeyVar(bossModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("boss:  %s   " % (bv,))
      spDaq = sr.getKeyVar(bossModel.daqVersion, ind=0,defVal=defVal)
      self.logWdg.addMsg("    boss.daq: %s   " % (spDaq,))
      spMv = sr.getKeyVar(bossModel.specMechVersion, ind=0, defVal=defVal)
      self.logWdg.addMsg("    boss.specMech: %s   " % (spMv,))

      gcameraModel = TUI.Models.getModel("gcamera")
      gcv = sr.getKeyVar(gcameraModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("gcamera: %s   " % (gcv,))

      guiderModel = TUI.Models.getModel("guider")
      gv = sr.getKeyVar(guiderModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("guider: %s   " % (gv,))

      hubModel = TUI.Models.getModel("hub")
      hubv = sr.getKeyVar(hubModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("hub: %s   " % (hubv,))

      mcpModel = TUI.Models.getModel("mcp")
      mcpv = sr.getKeyVar(mcpModel.mcpVersion, ind=0, defVal=defVal)
      self.logWdg.addMsg("mcp:  %s   " % (mcpv,))
      mcpPlc = sr.getKeyVar(mcpModel.plcVersion, ind=0, defVal=defVal )
      self.logWdg.addMsg("    mcp.plc:  %s   " % (mcpPlc,))
      self.logWdg.addMsg("    mcp.azFiducialVersion:  %s   "
            % (sr.getKeyVar(mcpModel.azFiducialVersion, ind=0, defVal=defVal)))
      self.logWdg.addMsg("    mcp.altFiducialVersion:  %s   "
            % (sr.getKeyVar(mcpModel.altFiducialVersion, ind=0, defVal=defVal)))
      self.logWdg.addMsg("    mcp.rotFiducialVersion:  %s   "
            % (sr.getKeyVar(mcpModel.rotFiducialVersion, ind=0, defVal=defVal)))

      pbvModel = TUI.Models.getModel("platedb")
      pbv = sr.getKeyVar(pbvModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("platedb: %s   " % (pbv,))

      sopModel = TUI.Models.getModel("sop")
      yield sr.waitCmd(actor="sop", 
          cmdStr="version", 
          keyVars=[sopModel.version],
          checkFail = False)
      cmdVar = sr.value
      if cmdVar.didFail: sopVers=defVal
      else: sopVers = sr.value.getLastKeyVarData(sopModel.version)[0]
      self.logWdg.addMsg("sop: %s   " % (sopVers,))

      sosModel = TUI.Models.getModel("sos")
      yield sr.waitCmd(actor="sos", 
           cmdStr="version",
           keyVars=[sosModel.version],
           checkFail = False,)
      cmdVar = sr.value
      if cmdVar.didFail: sosVers=defVal
      else:  sosVers = sr.value.getLastKeyVarData(sosModel.version)[0] 
      self.logWdg.addMsg("sos: %s   " % (sosVers,))

      yield sr.waitCmd(actor="sos", 
           cmdStr="status",
           keyVars=[sosModel.idlspec2dVersion],
           checkFail = False,)
      cmdVar = sr.value
      if cmdVar.didFail: sosVersIDL=defVal
      else:  sosVersIDL = sr.value.getLastKeyVarData(sosModel.idlspec2dVersion)[0] 
      self.logWdg.addMsg("sos.idlspec2d: %s   " % (sosVersIDL,))

# see Russell's instruction for STUI 5.2
      tccModel = TUI.Models.getModel("tcc")
      yield sr.waitCmd(actor="tcc", 
             cmdStr="show version", 
          #   keyVars=[tccModel.text],
             keyVars=[tccModel.version], 
             checkFail =False,)
      cmdVar = sr.value
      if cmdVar.didFail: tccVers=defVal
    #  else: tccVers = sr.value.getLastKeyVarData(tccModel.text)[0]
      else: tccVers = sr.value.getLastKeyVarData(tccModel.version)[0]
      self.logWdg.addMsg("tcc: %s   " % (tccVers,))

      apogeeModel = TUI.Models.getModel("apogee")
      apogeecalModel = TUI.Models.getModel("apogeecal")
      apogeeqlModel = TUI.Models.getModel("apogeeql")      
      defVal1="-not availble- "
      apogeeVer = sr.getKeyVar(apogeeModel.version, ind=0, defVal=defVal1)
      apogeecalVer = sr.getKeyVar(apogeecalModel.version, ind=0, defVal=defVal1)
      apogeeqlVer = sr.getKeyVar(apogeeqlModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("apogee:  %s" % (apogeeVer))
      self.logWdg.addMsg("apogeecal:  %s" % (apogeecalVer))
      self.logWdg.addMsg("apogeeql:  %s" % (apogeeqlVer))

  #    self.logWdg.addMsg(" ")

      self.logWdg.addMsg("-----Other software", tags=["g"])
      procVer=defVal 
      
 #     h1=httplib.HTTPConnection("sdsshost2.apo.nmsu.edu")
 #     h1.request("GET","/sdssProcedures/version.txt")
 #     http://sdss3.apo.nmsu.edu/sdssProcedures/version.txt
      srv="sdss3.apo.nmsu.edu"   # server
      pth="/sdssProcedures/version.txt"  # path
      h1=httplib.HTTPConnection(srv) 
      h1.request("GET",pth)
      procVer=h1.getresponse().read()
      h1.close()
      self.logWdg.addMsg("sdssProcedure(sdss3): %s   " % (str(procVer).rstrip()))
        
      vPath="/Library/Application Support/STUIAdditions/Scripts/APO-local/version.txt"
      if  os.path.isfile(vPath):             
          vFile=open(vPath, "r")
          scrVer=vFile.read()
          vFile.close()
      else: scrVer="not availble"
      self.logWdg.addMsg("APO-local scripts : %s   " % (str(scrVer).rstrip()))
      self.logWdg.addMsg("    -- done --", tags=["a"])

    def end(self, sr):        
      self.logWdg.addMsg("")
    


#   These are functions of the hub actor, not actors
#      self.logWdg.addMsg("keys  -- ?")
#      self.logWdg.addMsg("msg  --?")
#      self.logWdg.addMsg("perms  -- ?")
