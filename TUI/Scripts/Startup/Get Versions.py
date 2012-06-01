# 06/09/2010  Added defVal variable to check if fail
#   changed format of output from "actor --- ver " to "actor: ver"
# 08/20/2010 changed server name for sdssProcedure
# 05/16/2011  resizable window

import RO.Wdg
import TUI.Models
import TUI.Version
import httplib
from datetime import datetime

class ScriptClass(object):
    def __init__(self, sr):
        # if True, run in debug-only mode 
        # if False, real time run
        sr.debug = False
        sr.master.winfo_toplevel().wm_resizable(True, True)
        self.logWdg = RO.Wdg.LogWdg(
            master=sr.master,
            width=40,  height =30,
        )
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
    
    def run(self, sr):
      defVal="** FAILED **"

      ff=("Times", "17", "bold italic")
      fs="12"   # font size
      ft="Monaco" # "Courier"  #"Menlo"  # font type
      self.logWdg.text.tag_config("cur", font=(ft,fs,"bold")) 
      utc_datetime = datetime.utcnow()
      tm=utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
   #   print 'getVersions, %s ' % (tm)
      self.logWdg.addMsg('getVersions,  %s' % (tm), tags=["cur"])
      self.logWdg.addMsg(" ")

      self.logWdg.addMsg("----STUI software: ")
      tuiver=TUI.Version.VersionStr
   #   print "STUI: ", tuiver
      self.logWdg.addMsg("STUI: %s;  " % (tuiver))

      alertsModel =TUI.Models.getModel("alerts")
      alv = sr.getKeyVar(alertsModel.version, ind=0, defVal=defVal)
   #   print "alerts: "+alv
      self.logWdg.addMsg("alerts: %s;  " % (alv,))

      apoModel =TUI.Models.getModel("apo")
      apv = sr.getKeyVar(apoModel.version, ind=0, defVal=defVal)  
  #    yield sr.waitCmd(actor="apo", cmdStr="version",
  #          keyVars=[apoModel.version],checkFail = False,)
  #    cmdVar = sr.value
  #    if cmdVar.didFail:  apv=defVal 
  #    else:   apv = sr.value.getLastKeyVarData(apoModel.version)[0] 
   #   print "apo: "+str(apv)
      self.logWdg.addMsg("apo:  %s;  " % (apv,))

      bossModel = TUI.Models.getModel("boss")
      bv = sr.getKeyVar(bossModel.version, ind=0, defVal=defVal)
   #   print "boss: ", bv
      self.logWdg.addMsg("boss:  %s;  " % (bv,))
      spDaq = sr.getKeyVar(bossModel.daqVersion, ind=0,defVal=defVal)
    #  print "boss.daq: ", spDaq
      self.logWdg.addMsg("boss.daq: %s;  " % (spDaq,))
      spMv = sr.getKeyVar(bossModel.specMechVersion, ind=0, defVal=defVal)
    #  print "boss.specMechVersion: ", spMv
      self.logWdg.addMsg("boss.specMech: %s;  " % (spMv,))

      gcameraModel = TUI.Models.getModel("gcamera")
      gcv = sr.getKeyVar(gcameraModel.version, ind=0, defVal=defVal)
    #  print "gcamera: "+gcv
      self.logWdg.addMsg("gcamera: %s;  " % (gcv,))

      guiderModel = TUI.Models.getModel("guider")
      gv = sr.getKeyVar(guiderModel.version, ind=0, defVal=defVal)
    #  print "guider: ",gv
      self.logWdg.addMsg("guider: %s;  " % (gv,))

      hubModel = TUI.Models.getModel("hub")
      hubv = sr.getKeyVar(hubModel.version, ind=0, defVal=defVal)
   #   print "hub: ", hubv
      self.logWdg.addMsg("hub: %s;  " % (hubv,))

      mcpModel = TUI.Models.getModel("mcp")
      mcpv = sr.getKeyVar(mcpModel.mcpVersion, ind=0, defVal=defVal)
   #   print "mcp: "+mcpv
      self.logWdg.addMsg("mcp:  %s;  " % (mcpv,))
      mcpPlc = sr.getKeyVar(mcpModel.plcVersion, ind=0, defVal=defVal )
   #   print "mcp.plc: "+str(mcpPlc)
      self.logWdg.addMsg("mcp.plc:  %s;  " % (mcpPlc,))
      self.logWdg.addMsg("mcp.azFiducialVersion:  %s;  "
                         % (sr.getKeyVar(mcpModel.azFiducialVersion, ind=0, defVal=defVal)))
      self.logWdg.addMsg("mcp.altFiducialVersion:  %s;  "
                         % (sr.getKeyVar(mcpModel.altFiducialVersion, ind=0, defVal=defVal)))
      self.logWdg.addMsg("mcp.rotFiducialVersion:  %s;  "
                         % (sr.getKeyVar(mcpModel.rotFiducialVersion, ind=0, defVal=defVal)))

      pbvModel = TUI.Models.getModel("platedb")
      pbv = sr.getKeyVar(pbvModel.version, ind=0, defVal=defVal)
  #    print "platedb: "+pbv
      self.logWdg.addMsg("platedb: %s;  " % (pbv,))

      sopModel = TUI.Models.getModel("sop")
  #    sopVers = sr.getKeyVar(sopModel.version, ind=0, defVal=defVal)
      yield sr.waitCmd(actor="sop", 
          cmdStr="version", 
          keyVars=[sopModel.version],
          checkFail = False)
      cmdVar = sr.value
      if cmdVar.didFail: sopVers=defVal
      else: sopVers = sr.value.getLastKeyVarData(sopModel.version)[0]
  #    print "sop: "+sopVers
      self.logWdg.addMsg("sop: %s;  " % (sopVers,))

      sosModel = TUI.Models.getModel("sos")
  #    sosVers = sr.getKeyVar(sosModel.version, ind=0, defVal=defVal)  
      yield sr.waitCmd(actor="sos", 
           cmdStr="version",
           keyVars=[sosModel.version],
           checkFail = False,)
      cmdVar = sr.value
      if cmdVar.didFail: sosVers=defVal
      else:  sosVers = sr.value.getLastKeyVarData(sosModel.version)[0] 
  #    print "sos: "+sosVers
      self.logWdg.addMsg("sos: %s;  " % (sosVers,))

      yield sr.waitCmd(actor="sos", 
           cmdStr="status",
           keyVars=[sosModel.idlspec2dVersion],
           checkFail = False,)
      cmdVar = sr.value
      if cmdVar.didFail: sosVersIDL=defVal
      else:  sosVersIDL = sr.value.getLastKeyVarData(sosModel.idlspec2dVersion)[0] 
  #    print "sos.idlspec2d: "+sosVersIDL
      self.logWdg.addMsg("sos.idlspec2d: %s;  " % (sosVersIDL,))

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
  #    print "tcc: "+tccVers
      self.logWdg.addMsg("tcc: %s;  " % (tccVers,))

      apogeeModel = TUI.Models.getModel("apogee")
      apogeecalModel = TUI.Models.getModel("apogeecal")
      apogeeqlModel = TUI.Models.getModel("apogeeql")      
      apogeeVer = sr.getKeyVar(apogeeModel.version, ind=0, defVal=defVal)
      apogeecalVer = sr.getKeyVar(apogeecalModel.version, ind=0, defVal=defVal)
      apogeeqlVer = sr.getKeyVar(apogeeqlModel.version, ind=0, defVal=defVal)
      self.logWdg.addMsg("apogee:  %s" % (apogeeVer))
      self.logWdg.addMsg("apogeecal:  %s" % (apogeecalVer))
      self.logWdg.addMsg("apogeeql:  %s" % (apogeeqlVer))

      self.logWdg.addMsg(" ")

      self.logWdg.addMsg("-----Other software")
      procVer=defVal 
 #     h1=httplib.HTTPConnection("sdsshost2.apo.nmsu.edu")
 #     h1.request("GET","/sdssProcedures/version.txt")

 # http://sdss3.apo.nmsu.edu/sdssProcedures/version.txt
      srv="sdss3.apo.nmsu.edu" 
      pth="/sdssProcedures/version.txt"
      h1=httplib.HTTPConnection(srv)
      h1.request("GET",pth)

      procVer=h1.getresponse().read()
      h1.close()
  #    print "sdssProcedure: ", str(procVer).rstrip()
      self.logWdg.addMsg("sdssProcedure(sdss3): %s;  " % (str(procVer).rstrip()))
       #    print "sdssProcedure: ", str(procVer).rstrip()

        
#      self.logWdg.addMsg("------ ")
#      print "--- end getVersions.py --"  

#   These are functions of the hub actor, not actors
#      self.logWdg.addMsg("keys  -- ?")
#      self.logWdg.addMsg("msg  --?")
#      self.logWdg.addMsg("perms  -- ?")
