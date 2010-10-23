"""A sample script module for ScriptWdg.ScriptModuleWdg.

Counts up to a user-specified number with a user-specified
delay between each count.

The widgets that can be adjusted to control script behavior
while the script runs (a very good idea when offering widgets).

History:
2004-06-30 Rowen
"""
import RO.Wdg

def init(sr):
    """Run once when the script runner window is created.
    """
    gr = RO.Wdg.Gridder(sr.master)
    
    niterWdg = RO.Wdg.IntEntry(
        sr.master,
        minValue = 0,
        maxValue = 99,
        defValue = 10,
        helpText = "number of iterations",
    )
    gr.gridWdg("# Iter", niterWdg)
    
    delayWdg = RO.Wdg.FloatEntry(
        sr.master,
        minValue = 0,
        maxValue = 99,
        defValue = 0.5,
        defFormat = "%.1f",
        helpText = "delay between each iteration",
    )
    gr.gridWdg("Delay", delayWdg, "sec")
    
    sr.globals.niterWdg = niterWdg
    sr.globals.delayWdg = delayWdg

def run(sr):
    """The main script. Run when the Start button is pushed.
    
    The widgets are read each time through to give the user
    the maximum control. However, note that it is all too easy
    to accidentally set the delay to 0 (causing the script
    to finish instantly) while trying to adjust it.
    This sort of trap is best avoided in real scripts.
    """
    ii = 0
    while ii < sr.globals.niterWdg.getNum():
        ii+= 1
        sr.showMsg(str(ii))
        yield sr.waitMS(sr.globals.delayWdg.getNum() * 1000)
