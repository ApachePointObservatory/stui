import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("boss", delay=1.0)
tuiModel = testDispatcher.tuiModel

ExposeMainDataList = (
    "exposureState=IDLE, 0, 0",
    "hardwareStatus=0x38",
    "shutterStatus=0x1, 0x1",
    "screenStatus=0x5, 0x5",
    "motorPosition=5000, 4800, 5200, 3500, 3600, 3700",
    "motorStatus=0x1, 0x1, 0x1, 0x1, 0x1, 0x1",
)

ExposeAnimDataSet = (
    (
    "shutterStatus=0x0, 0x1",
    ),
    (
    "shutterStatus=0x0, 0x0",
    "screenStatus=0x1, 0x4",
    ),
    (
    "shutterStatus=0x2, 0x0",
    "screenStatus=0x9, 0x6",
    ),
    (
    "shutterStatus=0x2, 0x2",
    "screenStatus=0x0, 0x0",
    ),
    (
    "shutterStatus=0x2, 0x0",
    "screenStatus=0x6, 0x9",
    ),
    (
    "shutterStatus=0x0, 0x0",
    "screenStatus=0x4, 0x1",
    ),
    (
    "shutterStatus=0x0, 0x1",
    "screenStatus=0x5, 0x5",
    ),
    (
    "shutterStatus=0x3, 0x1",
    ),
    (
    "shutterStatus=0x1, 0x1",
    ),
)

def exposeStart():
    testDispatcher.dispatch(ExposeMainDataList)
    
def exposeAnimate(dataIter=None):
    testDispatcher.runDataSet(ExposeAnimDataSet)
