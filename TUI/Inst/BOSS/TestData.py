import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("boss", delay=1.0)
tuiModel = testDispatcher.tuiModel

ExposeMainDataList = (
)

ExposeAnimDataSet = (
    (
    ),
    (
    ),
)

def exposeStart():
    testDispatcher.dispatch(ExposeMainDataList)
    
def exposeAnimate(dataIter=None):
    testDispatcher.runDataSet(ExposeAnimDataSet)
