import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("perms", delay=1.5)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    "actors=dis, echelle, tcc, tlamps, tspec",
    "programs=UW01, CL01, TU01",
    "lockedActors=tspec",
    "authList=TU01, echelle, perms, tcc, tspec",
    "authList=CL01, tcc, dis, tspec, tlamps",
    "authList=UW01, tcc, echelle",
)

AnimDataSet = (
    (
        "authList=CL01, tcc, dis, echelle, tspec, tlamps",
        "authList=UW01, tcc, tspec, tlamps",
    ),
    (
        "programs=TU01, UW01",
    ),
    (
        "actors=tcc, tspec, dis, echelle, tlamps, apollo",
    ),
    (
        "authList=CL01, apollo, echelle, perms, tcc, tspec",
    ),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
