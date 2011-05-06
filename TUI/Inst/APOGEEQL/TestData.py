import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("apogeeql", delay=5)
tuiModel = testDispatcher.tuiModel

ICCDataList = (
    "utrReadTime=10",
)
MainDataList = (
    "snrGoal=30.0, 12.0",
    "exposureData=1001, 1, 00120009, 600.0, 5, 30.0,  0.0, 28.2,  600, 28.2",
    "exposureData=1001, 2, 00120010, 600.0, 5, 30.0,  0.5, 28.2, 1200, 39.9",
    "exposureData=1001, 3, 00120011, 600.0, 5, 30.0, -0.5, 28.2, 1800, 48.8",
    "exposureData=1001, 4, 00120012, 600.0, 5, 30.0,  0.5, 28.2, 2400, 56.4",
    "exposureData=1001, 5, 00120013, 600.0, 5, 30.0, -0.5, 28.2, 3000, 63.1",
    "exposureData=1001, 6, 00120014, 600.0, 5, 30.0,  0.5, 28.2, 3600, 69.1",
    "snrH12Target=30",
    "utrData=00120015, 1, 10.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0",
    "utrData=00120015, 2, 15.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0",
    "utrData=00120015, 3, 20.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0",
    "utrData=00120015, 4, 24.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 4.0",
    "snrAxisRange=14, 32",
)

AnimDataSet = (
    (
        "utrData=00120015, 5, 28.0, -99.05, 174.10, -98.70, 171.90, 15, 0.51, 0.50, 1.0, 633.0, 6, 6, 4.0",
    ),
)

def start():
    testDispatcher.dispatch(ICCDataList, actor="apogee")
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
