import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("apogeeql", delay=0.5)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    "exposureList=1001, 1, 00000113, 600.0, 5,  0.0, 28.2,  600, 28.2",
    "exposureList=1001, 2, 00000114, 600.0, 5,  0.5, 28.2, 1200, 39.9",
    "exposureList=1001, 3, 00000115, 600.0, 5, -0.5, 28.2, 1800, 48.8",
    "exposureList=1001, 4, 00000116, 600.0, 5,  0.5, 28.2, 2400, 56.4",
    "exposureList=1001, 5, 00000117, 600.0, 5, -0.5, 28.2, 3000, 63.1",
    "exposureList=1001, 6, 00000118, 600.0, 5,  0.5, 28.2, 3600, 69.1",
    "snrH12Target=30",
    "snrData=00000118, 1, 10",
    "snrData=00000118, 2, 15",
    "snrData=00000118, 3, 20",
    "snrData=00000118, 4, 24",
    "snrData=00000118, 5, 28",
    "snrAxisRange=14, 32",
)

AnimDataSet = (
    (
    ),
)

def start():
    print "dispatch MainDataList"
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
