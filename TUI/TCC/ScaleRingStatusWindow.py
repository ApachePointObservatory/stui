#!/usr/bin/env python
"""Displays the status of the mirrors.

2003-03-25 ROwen    first release
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-06-09 ROwen    Removed most args from addWindow
                    and dispatcher arg from MirrorStatsuWdg.
2003-06-25 ROwen    Fixed a keyword name error in the test case;
                    modified test case to handle message data as a dict.
2003-07-13 WKetzeback   Added commanded positions to the widget.
2003-07-22 ROwen    Modified to use gridder; abbreviated displayed labels
2003-12-16 ROwen    Fixed comments for addWindow.
2004-05-18 ROwen    Stopped importing string and sys since they weren't used.
2006-09-27 ROwen    Updated for new 5-axis secondary.
2009-04-01 ROwen    Modified for sdss TUI.
2009-07-19 ROwen    Modified to use KeyVar.addValueListCallback instead of addROWdgSet.
2009-11-05 ROwen    Added WindowName.
2010-03-12 ROwen    Changed to use Models.getModel.
2015-01-06 ROwen    Changed mount section for new TCC: show commanded actuator length,
                    measured encoder length and desired encoder length.
                    Added mirror state, including a countdown timer.
                    Added help text and a status bar to dispay it.
                    Removed some unused imports and variables.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import Tkinter
import RO.Wdg
import TUI.Base.Wdg
import TUI.Models

WindowName = "TCC.Threadring Status"

# NumPrimAxes = 6
# NumSecAxes = 5

_HelpURL = "Telescope/MirrorStatusWin.html"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+22",
        visible = False,
        resizable = False,
        wdgFunc = ScaleRingStatusWdg,
    )

class ScaleRingStatusWdg (Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """creates a new mirror status display frame

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master, **kargs)

        tccModel = TUI.Models.getModel("tcc")
        gr = RO.Wdg.Gridder(self)

        #
        # display mirror orientation
        #

        # orientation title, (precision, width) for each column
        # orientColInfo = (
        #     ("Pos (mm)", (2, 10)),
        #     ("Des Pos (mm)", (2, 10)),
        #     ("Zero Pos (mm)", (2, 10)),
        #     ("Speed (mm/sec)", (2, 10)),
        #     ("Cart Loaded ", (2, 10)),
        #     ("Cart Locked ", (2, 10)),
        # )

        # threadHelpStr = "Thread ring status"
        # orientKeyVarNames = ["ThreadRingPos", "DesThreadRingPos", "ScaleZeroPos", "ThreadRingSpeed", "CartLoaded", "CartLocked"]
        orientTitles =  ["Pos (mm)", "Target Pos (mm)", "Scale Zero Pos (mm)", "Speed (mm/sec)", "Cart Loaded", "Cart Locked"]
        # orientPrecWidthSet = [(2,8)]*6

        orientTitleWdgs = [RO.Wdg.StrLabel(self, text=label) for label in orientTitles]
        gr.gridWdg(
            label = "Orientation",
            dataWdg = orientTitleWdgs,
        )
        orientWdgSet = []
        posWdg = RO.Wdg.FloatLabel(
                    master = self,
                    precision = 2,
                    width = 8,
                    helpText = "Thread Ring Pos",
                    helpURL = _HelpURL,
                )

        orientWdgSet.append(posWdg)

        def setPos(keyVar, posWdg=posWdg):
            """Callback for thread ring position
            """
            pos = keyVar[0]
            posWdg.set(pos, isCurrent = keyVar.isCurrent)

        posVar = getattr(tccModel, "threadringPos")
        posVar.addCallback(setPos)

        desPosWdg = RO.Wdg.FloatLabel(
                    master = self,
                    precision = 2,
                    width = 8,
                    helpText = "Desired Thread Ring Pos",
                    helpURL = _HelpURL,
                )

        orientWdgSet.append(desPosWdg)

        def desSetPos(keyVar, desPosWdg=desPosWdg):
            """Callback for thread ring position
            """
            pos = keyVar[0]
            desPosWdg.set(pos, isCurrent = keyVar.isCurrent)


        desPosVar = getattr(tccModel, "desThreadringPos")
        desPosVar.addCallback(desSetPos)


        zeroWdg = RO.Wdg.FloatLabel(
                    master = self,
                    precision = 2,
                    width = 8,
                    helpText = "Threadring zero",
                    helpURL = _HelpURL,
                )

        orientWdgSet.append(zeroWdg)

        def setZero(keyVar, zeroWdg=zeroWdg):
            """Callback for thread ring position
            """
            speed = keyVar[0]
            zeroWdg.set(speed, isCurrent = keyVar.isCurrent)


        zeroVar = getattr(tccModel, "scaleZeroPos")
        zeroVar.addCallback(setZero)

        speedWdg = RO.Wdg.FloatLabel(
                    master = self,
                    precision = 2,
                    width = 8,
                    helpText = "Threadring speed",
                    helpURL = _HelpURL,
                )

        orientWdgSet.append(speedWdg)

        def setSpeed(keyVar, speedWdg=speedWdg):
            """Callback for thread ring position
            """
            speed = keyVar[0]
            speedWdg.set(speed, isCurrent = keyVar.isCurrent)


        speedVar = getattr(tccModel, "threadringSpeed")
        speedVar.addCallback(setSpeed)


        loadedWdg = RO.Wdg.StrLabel(
                    master = self,
                    # precision = 2,
                    width = 8,
                    helpText = "Cart Loaded",
                    helpURL = _HelpURL,
                )

        orientWdgSet.append(loadedWdg)

        def setLoaded(keyVar, loadedWdg=loadedWdg):
            """Callback for thread ring position
            """
            loaded = keyVar[0]
            loadedWdg.set(loaded, isCurrent = keyVar.isCurrent)


        loadedVar = getattr(tccModel, "cartLoaded")
        loadedVar.addCallback(setLoaded)

        lockedWdg = RO.Wdg.StrLabel(
                    master = self,
                    # precision = 2,
                    width = 8,
                    helpText = "Cart Locked",
                    helpURL = _HelpURL,
                )

        orientWdgSet.append(lockedWdg)

        def setLocked(keyVar, lockedWdg=lockedWdg):
            """Callback for thread ring position
            """
            locked = keyVar[0]
            lockedWdg.set(locked, isCurrent = keyVar.isCurrent)


        lockedVar = getattr(tccModel, "cartLoaded")
        lockedVar.addCallback(setLocked)

        gr.gridWdg (
                label = "Values",
                dataWdg = orientWdgSet
            )


        fullHelpText = "%s" % ("thread ring state.")
        keyVarName = "threadringState"
        stateFrame = Tkinter.Frame(self)

        stateWdg = RO.Wdg.StrLabel(
            master = stateFrame,
            helpText = fullHelpText,
            helpURL = _HelpURL,
        )
        stateWdg.grid(row=0, column=0)
        timerWdg = RO.Wdg.TimeBar(
            master = stateFrame,
            barLength = 50,
        )
        timerWdg.grid(row=0, column=1)
        timerWdg.grid_remove() # only show when needed
        gr.gridWdg(
            label = "Threadring State",
            dataWdg = stateFrame,
            colSpan = 4,
            sticky = "w",
            helpText = fullHelpText,
        )

        def setState(keyVar, stateWdg=stateWdg, timerWdg=timerWdg):
            """Callback for <mir>State; used to set state widgets for the appropriate mirror
            """
            severity = {
                "Done": RO.Constants.sevNormal,
                "Moving": RO.Constants.sevWarning,
                "Homing": RO.Constants.sevWarning,
                "Failed": RO.Constants.sevError,
                "NotHomed": RO.Constants.sevError,
                None: RO.Constants.sevWarning,
            }.get(keyVar[0], RO.Constants.sevWarning)
            if keyVar[0] is None:
                stateStr = "?"
            # elif keyVar[1]:
            #     stateStr = "%s: iter %s of %s" % (keyVar[0], keyVar[1], keyVar[2])
            # else:
            stateStr = keyVar[0]
            stateWdg.set(stateStr, severity = severity, isCurrent = keyVar.isCurrent)

            if keyVar.isCurrent and keyVar[4] > 0:
                timerWdg.start(value = keyVar[3], newMax = keyVar[4])
                timerWdg.grid()
            else:
                timerWdg.grid_remove()
                timerWdg.clear()
        stateVar = getattr(tccModel, keyVarName)
        stateVar.addCallback(setState)

        # self.statusWdg = TUI.Base.Wdg.StatusBar(self)
        # gr.gridWdg(False, self.statusWdg, colSpan=10, sticky="ew")


if __name__ == "__main__":
    import TUI.Base.TestDispatcher

    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
    tuiModel = testDispatcher.tuiModel
    root = tuiModel.tkRoot

    testFrame = MirrorStatusWdg(root)
    testFrame.pack()

    dataList = (
        "PrimOrient=205.26, 55.01, 0.95, 0.15, -21.05, 0",
        "PrimDesOrient=205.16, 54.99, 0.90, 0.35, -21.15, 0",
        "PrimEncMount=825550, 456400, 773050, 54541, 12532, 12532",
        "PrimDesEncMount=825550, 456400, 773050, 54541, 12532, 12532",
        "PrimCmdMount=825550, 456400, 773050, 54541, 12532, 12532",
        "PrimState=Moving, 2, 5, 25, 32",

        "SecOrient=105.26, -55.01, -0.95, -0.15, 21.05, 0",
        "SecDesOrient=105.16, -54.99, -0.90, -0.35, 21.15, 0.02",
        "SecEncMount=725528., 356362., 671055., 54300, 32150",
        "SecDesEncMount=725521., 356367., 671053., 54304, 32147",
        "SecCmdMount=725523., 356365., 671051., 54306, 32152",
        "SecState=Done, 0, 0, 0, 0",
    )
    testDispatcher.dispatch(dataList)

    tuiModel.reactor.run()
