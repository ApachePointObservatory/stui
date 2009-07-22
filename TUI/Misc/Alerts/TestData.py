import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("alerts", delay=1.0)
tuiModel = testDispatcher.tuiModel

MainDataList = (
    'alert=mcp.needIack, warn, "True", True',
    'alert=boss.tooWarm, critical, "30C", True',
)

AnimDataSet = (
    (
    'alert=boss.tooWarm, critical, "20C", True',
    ),
    (
    'alert=boss.tooWarm, info, "", True',
    ),
)

def start():
    testDispatcher.dispatch(MainDataList)
    
def animate(dataIter=None):
    testDispatcher.runDataSet(AnimDataSet)
