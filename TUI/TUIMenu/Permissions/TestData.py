#!/usr/bin/env python
"""Data for testing various DIS widgets"""
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("perms", delay=1.5)
tuiModel = testDispatcher.tuiModel

dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataList = (
    "actors=tcc, nicfps, dis, echelle, tlamps",
    "programs=UW01, CL01, TU01",
    "lockedActors=nicfps",
    "authList=TU01, tcc, nicfps, echelle, perms",
    "authList=CL01, tcc, dis, nicfps, tlamps",
    "authList=UW01, tcc, echelle",
)

# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
    (
        "authList=CL01, tcc, dis, echelle, nicfps, tlamps",
        "authList=UW02, tcc, nicfps, tlamps",
    ),
    (
        "programs=TU01, UW01",
    ),
    (
        "actors=tcc, nicfps, dis, echelle, tlamps, apollo",
    ),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
