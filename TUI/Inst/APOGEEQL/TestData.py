import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("apogeeql", delay=3)
tuiModel = testDispatcher.tuiModel

ICCDataList = (
    "utrReadTime=10",
)
MainDataList = (
    "snrGoal=30.0, 12.0",
    "exposureData=1001, 1, 00120009, 600.0, 5, 30.0,  0.0, 28.2,  600, 28.2, Object, ?",
    "exposureData=1001, 2, 00120010, 600.0, 5, 30.0,  0.5, 28.2, 1200, 39.9, Object, B",
    "exposureData=1001, 3, 00120011, 600.0, 5, 30.0, -0.5, 28.2, 1800, 48.8, Object, A",
    "exposureData=1001, 4, 00120012, 600.0, 5, 30.0,  0.5, 28.2, 2400, 56.4, Object, B",
    "snrH12Target=30",
    "utrData=00120013, 1, 10.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0, Object, B",
    "utrData=00120013, 2, 15.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0, Object, B",
    "utrData=00120013, 3, 20.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0, Object, B",
    "utrData=00120013, 4, 24.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 4.0, Object, B",
    "snrAxisRange=14, 32",
    "predictedExposure=1001, 5, 00120013, 600.0, 5, 30.0, Object, 0.5, A",
    "predictedExposure=1001, 6, 00120014, 600.0, 5, 30.0, Object, 0.5, B",
    "missingFibers=00120013, 4, 0",
)

AnimDataSet = (
    (
        "utrData=00120013, 5, 28.0, -99.05, 174.10, -98.70, 171.90, 15, 0.51, 0.50, 1.0, 633.0, 6, 6, 4.0, , Object, B",
        "missingFibers=00120013, 4, nan",
    ),
    (
        "missingFibers=00120013, 4, 3, 2, 57, 75",
    ),
)

def start():
    testDispatcher.dispatch(ICCDataList, actor="apogee")
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
