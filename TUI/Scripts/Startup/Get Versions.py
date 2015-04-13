''' Get  versions of operational software

 06/09/2010  Added defVal variable to check if fail
   changed format of output from "actor --- ver " to "actor: ver"
08/20/2010 changed server name for sdssProcedure
05/16/2011  resizable window
02/06/2013  refinement
08/21/2013  EM: changed script local library name, check is version file exist   
08/29/2013  EM: changed script local library name to APO-local
03/27/2014  EM: added blue color for branch, trunk  for magenta;  format for table 
09/26/2014  EM: deleted sos and sos.idlspec2d versions; added hurtmann.verson 
'''

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

        self.sr=sr
        
        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=30,  height =31,)
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.logWdg.text.tag_config("a", foreground="magenta") 
        self.logWdg.text.tag_config("g", foreground="darkblue") 

        fs="12"   # font size
        ft="Monaco" # "Courier"  #"Menlo"  # font type
        self.logWdg.text.tag_config("cur", font=(ft,fs))        
        self.width=13

        self.logWdg.text.tag_config("branch", foreground="blue")
        self.logWdg.text.tag_config("trunk", foreground="magenta")
         
#        fidCrossKeyVar = getattr(self.mcpModel, "%sFiducialCrossing" % (axisName.lower()))
#        def fidCrossCallFunc(fidCrossKeyVar, axisName=axisName):
#                self.axisFiducialCrossingCallback(axisName, fidCrossKeyVar)
#        fidCrossKeyVar.addCallback(fidCrossCallFunc, callNow=False)

    def getVer1Print(self, act, ver, defVal):
        act=act[:self.width]
        ss="%s : %s" % (act.ljust(self.width), ver)
        tags=["cur"]
        if "branch" in ver: tags.append("branch")  
        if "trunk" in ver:  tags.append("trunk")  
        if defVal==ver:
          self.logWdg.addMsg("%s"% (ss), severity=RO.Constants.sevError, tags=tags)
        else:  
          self.logWdg.addMsg("%s" % (ss), tags=tags)
    
    def getVer1(self, act, defVal="FAILED"):
        sr=self.sr        
        actModel =TUI.Models.getModel(act)
        ver = sr.getKeyVar(actModel.version, ind=0, defVal=defVal)
        self.getVer1Print(act, ver, defVal)
                            
    def run(self, sr):
      tm=datetime.utcnow().strftime("%D, %H:%M:%S")
      defVal="  FAILED"

      self.logWdg.clearOutput()  
      self.logWdg.addMsg("%s, %s" % (self.name, tm), tags=["a"]) 
      self.logWdg.addMsg("  -- STUI software: ", tags=["g"])
      self.getVer1Print("STUI", TUI.Version.VersionName, "")

#    if connected? 
  #    tuiModel = TUI.Models.getModel("tui")
  #    conn=tuiModel.getConnection()
  #    if conn:
  #         self.logWdg.addMsg("    STUI is not connected", severity=self.redWarn) 
  #         defVal="  n/a"
           
      self.getVer1("alerts")
      self.getVer1("apo")
      self.getVer1("boss")
      
      bossModel = TUI.Models.getModel("boss")
      #spDaq = sr.getKeyVar(bossModel.daqVersion, ind=0,defVal=defVal)
      spMv = sr.getKeyVar(bossModel.specMechVersion, ind=0, defVal=defVal)
      #self.getVer1Print("-boss.daq", spDaq,defVal)
      self.getVer1Print("-boss.specMechVersion", spMv, defVal)

      self.getVer1("gcamera")
      self.getVer1("guider")
      self.getVer1("hartmann")
      self.getVer1("hub")

      mcpModel = TUI.Models.getModel("mcp")
      mcpv = sr.getKeyVar(mcpModel.mcpVersion, ind=0, defVal=defVal)
      self.getVer1Print("mcp", mcpv, defVal)
            
      mcpPlc = sr.getKeyVar(mcpModel.plcVersion, ind=0, defVal=defVal )
      self.getVer1Print("-mcp.plc", str(mcpPlc), defVal)
                
      self.getVer1Print("-mcp.azFiducialVersion", \
           sr.getKeyVar(mcpModel.azFiducialVersion, ind=0, defVal=defVal), defVal)
      self.getVer1Print("-mcp.altFiducialVersion", \
           sr.getKeyVar(mcpModel.altFiducialVersion, ind=0, defVal=defVal), defVal)
      self.getVer1Print("-mcp.rotFiducialVersion", \
           sr.getKeyVar(mcpModel.rotFiducialVersion, ind=0, defVal=defVal), defVal)
           
      self.getVer1("platedb")
      self.getVer1("sop")
      
# see Russell's instruction for STUI 5.2
      tccModel = TUI.Models.getModel("tcc")
      yield sr.waitCmd(actor="tcc", 
             cmdStr="show version", 
          #   keyVars=[tccModel.text],
             keyVars=[tccModel.version], 
             checkFail =False,)
      cmdVar = sr.value
      if cmdVar.didFail: 
            tccVers=defVal
      else: 
            tccVers = sr.value.getLastKeyVarData(tccModel.version)[0]
      self.getVer1Print("tcc", tccVers, defVal)
      
      defVal1="not availble"

      apogeeModel = TUI.Models.getModel("apogee")
      apogeeVer = sr.getKeyVar(apogeeModel.version, ind=0, defVal=defVal1)
      self.getVer1Print("apogee", apogeeVer, "")
            
      apogeecalModel = TUI.Models.getModel("apogeecal")
      apogeecalVer = sr.getKeyVar(apogeecalModel.version, ind=0, defVal=defVal1)
      self.getVer1Print("apogeecal", apogeecalVer, "")
    
      self.getVer1("apogeeql")

      self.logWdg.addMsg("  -- Other software", tags=["g","cur"])
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
      self.getVer1Print("sdssProcedure", (str(procVer).rstrip()), defVal) 
        
      vPath="/Library/Application Support/STUIAdditions/Scripts/APO-local/version.txt"
      if  os.path.isfile(vPath):             
          vFile=open(vPath, "r");  scrVer=vFile.read(); vFile.close()
      else: scrVer="not availble"
      self.getVer1Print("APO-local", scrVer, "") 

    def end(self, sr):        
      self.logWdg.addMsg("  -- done --", tags=["g","cur"])
    
    
  #    yield sr.waitCmd(actor="apo", cmdStr="version",
  #          keyVars=[apoModel.version],checkFail = False,)
  #    cmdVar = sr.value
  #    if cmdVar.didFail:  apv=defVal 
  #    else:   apv = sr.value.getLastKeyVarData(apoModel.version)[0] 

