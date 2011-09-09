import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("apogeeql", delay=2)
tuiModel = testDispatcher.tuiModel

ICCDataList = (
    "utrReadTime=10",
)
MainDataList = (
    "snrGoal=30.0, 12.0",
    "snrH12Target=30",
    "utrData=00120013, 1, 10.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0, Object, B",
    "utrData=00120013, 2, 15.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0, Object, B",
    "utrData=00120013, 3, 20.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 5.0, Object, B",
    "utrData=00120013, 4, 24.0, -99.05, 174.10, -98.70, 171.90, 0, 0.51, 0.50, 1.0, 633.0, 6, 6, 4.0, Object, B",
    "snrAxisRange=14, 32",
    "missingFibers=00120013, 4, 0",
)

AnimDataSet = (
    (
        "exposureData=1002, 1, 00120009, 600.0, 5, 30.0,  0.0, 28.2,  600, 28.2, Object, ?",
        "utrData=00120013, 5, 28.0, -99.05, 174.10, -98.70, 171.90, 15, 0.51, 0.50, 1.0, 633.0, 6, 6, 4.0, , Object, B",
        "missingFibers=00120013, 4, nan",
    ),
    (
        "predictedExposure=1002, 2, 00120013, 600.0, 5, 30.0, Object, 0.5, A",
        "predictedExposure=1002, 3, 00120014, 600.0, 5, 30.0, Object, 0.5, B",
        "predictedExposure=1002, 4, 00120014, 600.0, 5, 30.0, Object, 0.5, B",
        "predictedExposure=1002, 5, 00120013, 600.0, 5, 30.0, Object, 0.5, A",
        "predictedExposure=1002, 6, 00120014, 600.0, 5, 30.0, Object, 0.5, B",
        "missingFibers=00120013, 4, 3, 2, 57, 75",
    ),
    (
        "predictedExposure=1003, 4, 00120014, 600.0, 5, 30.0, Object, 0.5, B",
        "predictedExposure=1003, 5, 00120013, 600.0, 5, 30.0, Object, 0.5, A",
        "predictedExposure=1003, 6, 00120014, 600.0, 5, 30.0, Object, 0.5, B",
        "missingFibers=00120013, 4, 3, 2, 57, 75",
    ),
)

def start():
    testDispatcher.dispatch(ICCDataList, actor="apogee")
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
