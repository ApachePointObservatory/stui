"""
02/13/2013  copied from goto6mcpV4-5

  10/25/2012  by EM
  move telescope to desAlt using MCP
  11/18/2012  - changed timeout from 40 sec to 80 sec
 01/04/2013  - changed time rate from 1 sec to 0.4 sec; output every second output; 
    review of pos and velocity faster by reorganization of check block;
    predicted new position by  (velocity)*(time interval) and stop if out of range.  
 01/08/2013  - call say from subprocess but not from os;  calculate predicted value
 of alt and stop if the next linear destination go below it;  output predicted alt; 
 change log style 
  01/09/2013 - add +-0.5 degrees behind destination, make room to finish naturally
  01/23/2013  1) removed tcc 'axis init' from the end;  
  2) changed "mcp alt move 6" to 
       "mcp alt goto_pos_va %s 300000 20000" % (self.altDes*3600/0.01400002855); 
 02/12/2013  changed condition to stop: stop if go down and 
 elif  pos<(self.altDes+(self.alt-self.altDes)*0.2) and abs(vel)>=abs(velold):
05/17/2013 EM  check host name and rise an error if not telescope laptop 
06/17/2014 EM changed getBit(self, key, name, val) function for new stui 1.4
08/19/2014 EM changed low limit from 6 to 5 degrees after summer shakedown
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import RO.Wdg
import Tkinter
import TUI.Models
import os
import time
import subprocess
import socket

class ScriptClass(object):
    def __init__(self, sr):
        sr.debug = False  # if False, real time run
    #    sr.debug = True  # if True, run in debug-only mode
        
        self.name="goto5mcp "         
        self.sr = sr
        sr.master.winfo_toplevel().wm_resizable(True, True)

        F1 = Tkinter.Frame(sr.master)
        gr1a = RO.Wdg.Gridder(F1)

        self.lowLimit=5
        self.altWdg = RO.Wdg.IntEntry(master =F1, defValue = 30,
             minValue = self.lowLimit, maxValue = 90, helpText = "Destination altitude ",)
        gr1a.gridWdg("Destination altitude: ", self.altWdg,)
        F1.grid(row=0, column=0, sticky="w")

        self.logWdg = RO.Wdg.LogWdg(master=sr.master,  width=35, height =20,)
        self.logWdg.grid(row=1, column=0, sticky="news")        
        sr.master.rowconfigure(1, weight=1)
        sr.master.columnconfigure(0, weight=1)
        
        self.tccModel = TUI.Models.getModel("tcc")
        self.mcpModel = TUI.Models.getModel("mcp")
                
        self.ab_I6_L0=['alt_mtr_up_perm_in', 'alt_mtr_dn_perm_in', 'alt_mtr1_perm_in', 'alt_mtr2_perm_in', 'wind_alt_mtr_perm_in', 'alt_plc_perm_in', 'wind_alt_plc_perm_in', 'az_stow_3a', 'az_mtr_cw_perm_in', 'az_mtr_ccw_perm_in', 'az_mtr1_perm_in', 'az_mtr2_perm_in', 'wind_az_mtr_perm_in', 'az_plc_perm_in', 'wind_az_plc_perm_in', 'az_stow_3b', 'tcc_stop', 'cr_stop', 'spare_s1_c2', 'fiber_signal_loss', 'n_wind_stop', 'n_fork_stop', 'n_rail_stop', 's_rail_stop', 'w_rail_stop', 'n_lower_stop', 's_lower_stop', 'e_lower_stop', 'w_lower_stop', 's_wind_stop', 'nw_fork_stop', 'mcp_watchdog_timer', ]
        self.ab_I7_L0=['alt_grt_83_limit_1', 'bldg_clear_alt', 'az_stow_2a', 'az_stow_2b', 'deg_15_stop_ext', 'alt_grt_18d6_limit_2', 'alt_slip', 'alt_velocity_limit', 'az_dir_cw', 'az_dir_ccw', 'az_neg_201a_cw', 'az_pos_445a_ccw', 'az_neg_201b_cw', 'az_pos_445b_ccw', 'spare_s8_c6', 'spare_s8_c7', 'rot_mtr_cw_perm_in', 'rot_mtr_ccw_perm_in', 'rot_mtr_perm_in', 'spare_s5_c3', 'bldg_perm_in', 'rot_plc_perm_in', 'hatch_cls', 'alt_les_2d5_limit', 'alt_grt_0d3_limit', 'alt_locking_pin_out', 'alt_les_90d5_limit', 'bldg_on_alt', 'az_109_131_limit_1', 'alt_grt_18d6_limit_1', 'az_stow_1a', 'az_stow_1b', ]
        self.ab_I9_L0=['s1_c0_bypass_sw', 's1_c1_bypass_sw', 's1_c2_bypass_sw', 's1_c3_bypass_sw', 's1_c4_bypass_sw', 's1_c5_bypass_sw', 's1_c6_bypass_sw', 's1_c7_bypass_sw', 's2_c0_bypass_sw', 's2_c1_bypass_sw', 's2_c2_bypass_sw', 's2_c3_bypass_sw', 's2_c4_bypass_sw', 's2_c5_bypass_sw', 's2_c6_bypass_sw', 's2_c7_mcp_wtchdg_byp', 't_bar_tel_stat', 'clamp_en_stat', 'clamp_dis_stat', 'az_brake_en_stat', 'az_brake_dis_stat', 'alt_brake_en_stat', 'alt_brake_dis_stat', 'low_lvl_lighting_req', 'solenoid_engage_sw', 'alt_locking_pin_in', 'in_9_bit_10_spare', 'in_9_bit_11_spare', 'in_9_bit_12_spare', 'in_9_bit_13_spare', 'in_9_bit_14_spare', 'in_9_bit_15_spare',]

        self.MaxPosErr = 0.01 # alt maximum position error (deg)
        self.azErr=0.2  
        self.timeInt= 0.4*1000 # 0.4 * 1000 sec
        self.TimeLimit = 80  # time limit for move to final altitude (80 sec)
        
        self.owMcp="(telnet):-1:"
  
    def getTAITimeStr(self,):
        ''' get TAI time for time-stamps'''
        return time.strftime("%H:%M:%S",
           time.gmtime(time.time() - RO.Astro.Tm.getUTCMinusTAI()))       

    def prnMsg (self, ss):
        ''' output time-stamp and message'''    
        self.logWdg.addMsg(ss)

    def semOwner(self,):
        ''' get semaphoreOwner from mcp'''
        sr=self.sr  
        ow = sr.getKeyVar(self.mcpModel.semaphoreOwner, ind=0, defVal=None)
        #  ow= self.mcpModel.semaphoreOwner[0] 
        return ow

    def ifBrakesOn(self,):
        ''' check if alt brakes on ? '''
        alt_brake=self.getBit(self.ab_I9_L0,"alt_brake_en_stat",self.mcpModel.ab_I9_L0[0])
        return alt_brake

    def ifAzStow1(self,):
        ''' check if az position in stow 121 ? ''' 
        az_stow1a=self.getBit(self.ab_I7_L0,"az_stow_1a",self.mcpModel.ab_I7_L0[0])
        az_stow1b=self.getBit(self.ab_I7_L0,"az_stow_1b",self.mcpModel.ab_I7_L0[0])    
        return (az_stow1a and az_stow1b)

    def getBit1(self, key, name, val):
        ''' get plc bit, my old version, do not use now '''
        ind=key.index(name)        
        mask=hex( int("1"+"0"*ind,2)  )
        if  val & int(mask,16) !=0:  
            rr=1
        else:  
            rr=0
        return rr

    def getBit(self, key, name, val):
        ''' get plc bit,  new version suggested by RO'''
        ind=key.index(name)
        mask = 1 << ind
        if  val & mask !=0:
            rr=1
        else:
           rr=0
        return rr

    def run(self, sr, sel=0):    
        ''' main program to goto5 '''
        
        # check settings 
        
        # is telescope laptop? 
        host=socket.gethostname()
        if not  ('25m-macbook' in host):
              self.prnMsg("goto5mcp should run on telescope laptop only")
              raise sr.ScriptError("not right computer") 
        tm= self.getTAITimeStr()   
        self.altDes=self.altWdg.getNum()  # destination altDes from self.altWdg         
        self.prnMsg("%s  Start the move to %s " % (tm, self.altDes))  

        # is alt brakes?  
        if self.ifBrakesOn():
            mes="clear altitude brake and run again"
            os.popen('say %s ' % (mes) )  # say mes
            raise sr.ScriptError(mes) 

        #  my debug set: True - run, False - skip the command 
        self.run1=True #  tcc axis stop 
        self.run2=True #  mcp sem_take 
        self.run3=True  #  mcp alt move
        self.run5=True #  mcp alt brake.on 
        self.run6=True  #  mcp sem_give 

        # sem owners 
        owTcc="TCC:0:0"
        owNone="None"
        owMcpGui="observer@sdsshost2.apo.nmsu.edu"
        
        ow=self.semOwner()
        if owMcpGui in ow: 
            raise sr.ScriptError(" please release MCP GUI semaphore and run again")
        if not ( (ow==owTcc) or (ow==owNone) or (self.owMcp in ow) ):
             raise sr.ScriptError("unknown semaphore owner,  exit")              
        self.prnMsg("semaphoreOwner = %s" % ow)
 
        # check axis status        
        yield sr.waitCmd(actor="tcc", cmdStr="axis status", 
            keyVars=[self.tccModel.altStat, self.tccModel.azStat, self.tccModel.rotStat,
                     self.tccModel.axePos],)
        # self.az, self.alt, self.rot = self.tccModel.axePos[0:3]   
        self.alt=sr.value.getLastKeyVarData(self.tccModel.altStat)[0]   
        self.az =sr.value.getLastKeyVarData(self.tccModel.azStat)[0]   
        self.rot=sr.value.getLastKeyVarData(self.tccModel.rotStat)[0] 
          
        self.prnMsg("az=%6.2f,  alt=%5.2f,  rot=%6.2f" % (self.az, self.alt,self.rot))                          
        if (self.az is None) or (self.alt ==None) or (self.rot is None):
            raise sr.ScriptError("some of axis are not availble,  exit")       
        if self.ifAzStow1() != 1:
            raise sr.ScriptError("plc: az is not at stow,  exit")
        if abs(self.az - 121.0 ) >= self.azErr:
            raise sr.ScriptError("tcc: az is not 121,  exit") 
             
        # get the direction of the move, direct=Up,Down, or None
        # from init section -  self.MaxPosErr = 0.01 # alt maximum position error (deg)
        if  abs(self.alt - self.altDes) < self.MaxPosErr:
            self.prnMsg(" alt == altDes, exit")
            os.popen('say %s ' % "telescope at destination, exit")  # say mes
            direct="None" 
            #return
            raise sr.ScriptError() 
        elif self.altDes  > self.alt: 
            direct="Up"
        elif self.altDes < self.alt: 
            direct="Down"
        else: 
            raise sr.ScriptError("where to go? exit")     
        self.prnMsg("alt=%s  --> altDes=%s,  %s" % (self.alt, self.altDes,  direct))
        
        os.popen('say %s ' % ("goto " + str(self.altDes)) )  # say mes

        #  Action section 

        # it owner == TCC,  "tcc axis stop"
        if self.semOwner()==owTcc: 
            act="tcc";   cmd="axis stop";  
            self.prnMsg("%s   %s .." % (act, cmd))
            if self.run1:   
               yield sr.waitCmd(actor=act, cmdStr=cmd)
               yield sr.waitMS(500)
               it=0
               while self.semOwner() != owNone:
                   yield sr.waitMS(500)
                   it=it+1
                   if it > 10: 
                        raise sr.ScriptError("tcc axis stop - failed, exit") 
               if self.semOwner() != owNone:
                    self.prnMsg("%s   %s .." % (self.semOwner(), owNone))
                    raise sr.ScriptError("tcc axis stop - failed, exit") 
                
        #  it owner is None,  "mcp sem_take" 
        if self.semOwner()=="None": 
            act="mcp";   cmd="sem_take";  
            self.prnMsg("%s  %s .." % (act, cmd))  
            if self.run2:     
               yield sr.waitCmd(actor=act, cmdStr=cmd, keyVars=[self.mcpModel.semaphoreOwner],)
               it=0
               while not (self.owMcp in self.semOwner()):
                   yield sr.waitMS(500)
                   it=it+1
                   if it > 10: 
                        raise sr.ScriptError("mcp sem_take - failed, exit")
                
        # check, is semOwner in owMcp="(telnet):-1:" ?
        ow= self.semOwner()
        if not (self.owMcp in ow):       
            raise sr.ScriptError("mcp did not get semaphore - failed")  

        #  move  "mcp alt move %s" % (altDes)              
        dtold=0;  velold=0;         
        startTime = time.time()  
        act="mcp";   
        # cmd="alt move %s" % (self.altDes);  
        cmd="alt goto_pos_va %s 300000 20000" % (self.altDes*3600./0.01400002855)       
        self.prnMsg("%s  %s .." % (act, cmd)) 
        if self.run3:
            yield sr.waitCmd(actor=act, cmdStr=cmd)

        #  watch for moving progress  
        i=0 
        while True:
            yield sr.waitMS(self.timeInt)
            yield sr.waitCmd(actor="tcc", cmdStr="axis status", \
                keyVars=[self.tccModel.altStat, self.tccModel.axePos],)
                #   pos = self.tccModel.axePos[1]
                #   pos, vel = self.tccModel.altStat[0:2]
            pos, vel = sr.value.getLastKeyVarData(self.tccModel.altStat)[0:2]               
            dt=time.time() - startTime
            nextAlt=pos+vel*(dt-dtold) 

            ssPos="%s,  %5.2f sec,   alt =%5.2f --> %5.2f,  vel=%5.2f" %  (i, dt, pos, nextAlt, vel)  
            if i%2==0:
                ssPos1="alt =%5.2f     vel=%5.2f" %  (pos, vel) 
                self.prnMsg(ssPos1)            
                subprocess.Popen(['say',str(int(round(pos)))])
            else:
                tm= self.getTAITimeStr()   
                    
            mes="" # request to break
            
            if abs(pos - self.altDes) < self.MaxPosErr:
                mes="moved to destination, brake"
                self.prnMsg(mes)
                break
            
            if direct=="Down":
                if nextAlt < (self.altDes-0.5):
                    self.prnMsg(ssPos) 
                    mes="next move too low - brake"
                    self.prnMsg(mes)
                    break                           
                elif pos < self.altDes:
                    self.prnMsg(ssPos) 
                    mes="moved too low - brake"
                    self.prnMsg(mes)
                    break                           
                elif pos < self.lowLimit:
                    self.prnMsg(ssPos)
                    mes="alt below %s - brake" % self.lowLimit
                    self.prnMsg(mes)
                    break                           
                elif  pos<(self.altDes+(self.alt-self.altDes)*0.2) and abs(vel)>=abs(velold):
                    self.prnMsg(ssPos)
                    mes="move did not decelerate, brake"
                    self.prnMsg(mes)
                    break                           

            if self.ifBrakesOn(): 
                mes="alt brake detected,  stop"
                self.prnMsg(mes);  break 
                               
            if direct == "Up":
                if nextAlt > (self.altDes+0.5):
                    self.prnMsg(ssPos)
                    mes="next move too high - brake"
                    self.prnMsg(mes)
                    break                           
                elif pos >  self.altDes:
                    self.prnMsg(ssPos)        
                    mes="moved too high - brake"
                    self.prnMsg(mes)
                    break     

            if dt > self.TimeLimit:
                mes="timeout, brake"
                self.prnMsg(mes)
                break

            i = i+1
            dtold = dt
            velold = vel

        #  if  semOwn=mcp but alt brake.off, call alt brake.on
        if (self.owMcp in self.semOwner()) and not self.ifBrakesOn():
            act="mcp"
            cmd="alt brake.on" 
            self.prnMsg("%s  %s .." % (act, cmd)) 
            if self.run5: 
                yield sr.waitCmd(actor=act, cmdStr=cmd, checkFail=False)
        os.popen('say %s ' % (mes) )  # say mes
                
        #  if semOwn = mcp, release sem to None
        if  self.owMcp in self.semOwner():
           act="mcp"
           cmd="sem_give"
           self.prnMsg("%s  %s .." % (act, cmd)) 
           if self.run6:
              yield sr.waitCmd(actor=act, cmdStr=cmd, checkFail=False)

        yield sr.waitCmd(actor="tcc", cmdStr="axis status", keyVars=[self.tccModel.altStat])
        pos, vel = sr.value.getLastKeyVarData(self.tccModel.altStat)[0:2] 
        self.prnMsg("final alt = %s,  velocity = %s .." % (pos, vel)) 
        yield sr.waitCmd(actor="tcc", cmdStr="axis stop")         
            
            
    def end(self, sr):
        """Clean up"""
        if  self.owMcp in self.semOwner():
           act="mcp"; cmd="sem_give";  
           sr.startCmd(actor=act, cmdStr=cmd, checkFail=False) 
        self.logWdg.addMsg("="*20)
