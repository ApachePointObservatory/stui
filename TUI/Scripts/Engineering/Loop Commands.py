"""Run a sequence of commands as a loop. 

The number of cycles write to entry window. 
The first large window is for the sequence of commands. 
Commands should be <actor> <command> 
The second large window is for timestamps, echo of commands, loop information. 
Blank lines and lines beginning with # are ignored.
 
Example: 
tcc show time
tui wait 3

Click Start to run and get: 

-- start sycle --
   1 (3)   ---   00:01:58
tcc show time 
tui wait 3 
   2 (3)   ---   00:02:02
tcc show time 
tui wait 3 
   3 (3)   ---   00:02:05
tcc show time 
tui wait 3 
----------- end sycle --

The idea is by KP,  looked at  Run_Commands.py as  an example. 

History: 
2014-02-07 - 1st working version added to APO-local trunk
2014-02-13 - refinement, create border around logs, titles of windows, number of cycles. 
2014-09-26 EM:  moved to STUI  Scripts/Engineering
2014-09-30 ROwen    minor cleanups
"""
import RO.Wdg
import Tkinter
import time

HelpURL = None
CurrCmdTag = "currCmd"

class ScriptClass(object):
    def __init__(self, sr, ):  
        # if True, run in debug-only mode 
        # if False, real time run
        sr.debug = False

        self.name="loop commands"
        
        sr.master.winfo_toplevel().wm_resizable(True, True)

        row=0
        self.lab = RO.Wdg.Label(master=sr.master, bd=1, text ="---- Commands to repeat ----")
        self.lab.grid(row=row, column=0, sticky="n") 
        
        row=row+1
        self.npWdg = RO.Wdg.IntEntry(master =sr.master, defValue = 1,
             minValue =1, maxValue =100, helpText ="Number of repeats", label = "label")
        self.npWdg.grid(row=row, column=0, sticky="n")
        
        row=3
        self.textWdg = RO.Wdg.Text(master=sr.master,width = 20,  height = 5,
      #      yscrollcommand = self.yscroll.set,  
            borderwidth = 1,  highlightbackground="grey",relief = "sunken", \
            helpText = "Commands to repeat", )
        self.textWdg.grid(row=row, column=0, sticky="nsew")  
        self.textWdg.tag_configure(CurrCmdTag, relief = "raised", 
             borderwidth = 1, foreground="black", background="lightgreen")  
               
        self.yscroll = Tkinter.Scrollbar(master = sr.master, 
                orient = "vertical",command=self.textWdg.yview)
        self.textWdg.config(yscrollcommand=self.yscroll.set)
        self.yscroll.grid(row=row, column=1, sticky="nsew")


        row=row+1
        self.lab = RO.Wdg.Label(master=sr.master, bd=1, text ="---- Log ----")
        self.lab.grid(row=row, column=0, sticky="n")       
        
        row=row+1
        self.logWdg = RO.Wdg.LogWdg(master=sr.master, width=20,height =10, 
            borderwidth =1,  highlightbackground="red",  relief = "sunken",) 
        self.logWdg.grid(row=row, column=0, sticky="nsew", columnspan=2)        
        self.logWdg.text.tag_config("nov", background="beige")
        self.logWdg.text.tag_config("a", foreground="magenta")

        sr.master.rowconfigure(3, weight=1)
        sr.master.rowconfigure(5, weight=1)
        sr.master.columnconfigure(0, weight=1)

    def getTAITimeStr(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      currTAITuple = time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      taiTimeStr = time.strftime("%H:%M:%S", currTAITuple) 
      taiDateStr = time.strftime("%Y-%m-%d", currTAITuple) 
      return taiTimeStr, taiDateStr

    def run(self, sr):
        self.logWdg.addMsg("-- start sycle --", tags=["a"])
        
        self.textWdg.focus_get()
   #     textStr = self.getData()
        textStr =self.textWdg.get("0.0", "end")
        textList = textStr.split("\n")
        
        n=self.npWdg.getNum()  # number of points

        for i in range(n):
          taiTimeStr, taiDateStr = self.getTAITimeStr()
          self.logWdg.addMsg("   %s (%s)   ---   %s" % (i+1,n, taiTimeStr))
          lineNum = 0
          for line in textList[0:]:
            lineNum += 1
            line = line.strip()
            if not line or line.startswith("#"):
                continue
        
            ind = "%d.0" % lineNum
            self.textWdg.tag_remove(CurrCmdTag, "0.0", "end")
            self.textWdg.tag_add(CurrCmdTag, ind, ind + " lineend")
            self.textWdg.see(ind)
            sr.showMsg("Executing: %s" % (line,))
            self.textWdg["state"] = "disabled"
            try: 
                actor, cmdStr = line.split(None, 1)
            except ValueError:
                actor=line
                cmdStr=None
            self.logWdg.addMsg("%s %s " % (actor, cmdStr), tags=["nov"])
            if actor.lower() != "tui":
                yield sr.waitCmd(actor = actor,  cmdStr = cmdStr,)
               # pass
            else:
                params = cmdStr.split()
                if len(params)==0:
                    raise sr.ScriptError("No tui command specified")
                if params[0].lower() == "wait":
                    if len(params) != 2:
                        raise sr.ScriptError("tui wait requires one parameter: time (in sec)")
                    waitSec = float(params[1])
                    yield sr.waitMS(waitSec * 1000)
                else: 
                    raise sr.ScriptError("Unreconized tui command: %r" % (cmdStr,))       
        
    def end(self, sr): 
        if not sr.didFail:
            self.textWdg.tag_remove(CurrCmdTag, "0.0", "end")       
        self.textWdg["state"] = "normal"
        self.logWdg.addMsg("----------- end sycle --\n",tags=["a"])
        
