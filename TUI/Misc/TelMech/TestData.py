#!/usr/bin/env python
import RO.Alg
import RO.ParseMsg
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()
Actor = "telmech"

MainData = (
    "device=heaters; h8=off; h24=off; h12=off; h20=off; h16=off; h4=off",
    "device=covers; covers=close",
    "device=tertrot; tertrot=na2",
    "device=eyelids; tr4=?; na2=?; na1=?; tr1=?; tr3=?; tr2=?; bc1=?; bc2=?",
    "device=louvers; rup=close; rmid=close; rlow=close; floor=close; lup=close; lmid=close; llow=close; stairw=close; lpit=close; rpit=close",
    "device=lights; catwalk=on;  fhalides=on; rhalides=on; platform=on; incand=on; int_incand=on; int_fluor=on;stairs=on",
    "device=shutters; right=close; left=close",
    "device=fans; intexhaust=off; press=on; telexhaust=off",
)

# each element of animDataSet is a reply to be dispatched, minus actor and type.
AnimDataSet = (
    "device=shutters; right=open; left=open",
    "device=covers; covers=open",
    "device=tertrot; tertrot=?",
    "device=tertrot; tertrot=tr1",
    "device=fans; press=off; intexhaust=on; telexhaust=on",
    "device=lights; catwalk=off; fhalides=off; rhalides=off; platform=off; incand=off; int_incand=on; int_fluor=on; stairs=off",
    "device=lights; catwalk=off; fhalides=off; rhalides=off; platform=off; incand=off; int_incand=on; int_fluor=off; stairs=off",
    "device=lights; catwalk=off; fhalides=off; rhalides=off; platform=off; incand=off; int_incand=off; int_fluor=off; stairs=off",
    "device=louvers; rup=close; rmid=close; rlow=close; floor=close; lup=open; lmid=open; llow=open; lpit=open; rpit=open; stairw=open",
    "device=louvers; rup=open; rmid=open; rlow=open; floor=open; lup=open; lmid=open; llow=open; lpit=open; rpit=open; stairw=open",
    "device=heaters; h8=on; h24=on; h12=on; h20=off; h16=off; h4=off",
    "device=heaters; h8=on; h24=on; h12=on; h20=on; h16=on; h4=on",
)

def dispatch(dataStr, cmdr=cmdr, actor=Actor, cmdID=1, msgType="i"):
    """Dispatch a message"""
    msgStr = "%s %s %s %s %s" % (cmdr, cmdID, actor, msgType, dataStr)
    msgDict = RO.ParseMsg.parseHubMsg(msgStr)
    print "Dispatching:", msgStr
    dispatcher.dispatch(msgDict)
    
def animate(dataIter=None):
    if dataIter == None:
        dataIter = iter(AnimDataSet)
    try:
        data = dataIter.next()
    except StopIteration:
        return
    dispatch(data)
    
    tuiModel.root.after(1500, animate, dataIter)

def run():
    for dataStr in MainData:
        dispatch(dataStr)
    animate()