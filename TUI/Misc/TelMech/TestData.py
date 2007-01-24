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
    "device=enable; telescope=off",
    "device=eyelids; tr4=?; na2=?; na1=?; tr1=?; tr3=?; tr2=?; bc1=?; bc2=?",
    "device=louvers; rup=close; rmid=close; rlow=close; floor=close; lup=close; lmid=close; llow=close; lpit=close; rpit=close",
    "device=lights; catwalk=off; rhalides=on; int_incand=on; platform=off; incand=on; int_fluor=on; fhalides=on; stairs=on",
    "device=covers; value=?",
    "device=shutters; right=close; left=close",
    "device=fans; intexhaust=off; press=on; telexhaust=off",
    "device=tertrot; value=?",
)

# each element of animDataSet is a reply to be dispatched, minus actor and type.
AnimDataSet = (
    "device=shutters; right=open; left=open",
    "device=enable; telescope=off",
    "device=fans; press=off; intexhaust=on; telexhaust=on",
    "device=lights; catwalk=off; rhalides=off; int_incand=on; platform=off; incand=off; int_fluor=on; fhalides=off; stairs=off",
    "device=lights; catwalk=off; rhalides=off; int_incand=off; platform=off; incand=off; int_fluor=off; fhalides=off; stairs=off",
    "device=louvers; rup=open; rmid=open; rlow=open; floor=open; lup=open; lmid=open; llow=open; lpit=open; rpit=open",
    "device=heaters; h8=on; h24=on; h12=on; h20=off; h16=off; h4=off",
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