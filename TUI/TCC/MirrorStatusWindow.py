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

WindowName = "TCC.Mirror Status"

NumPrimAxes = 6
NumSecAxes = 5

_HelpURL = "Telescope/MirrorStatusWin.html"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+22",
        visible = False,
        resizable = False,
        wdgFunc = MirrorStatusWdg,
    )

class MirrorStatusWdg (Tkinter.Frame):
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
        orientColInfo = (
            (u"Piston (\N{MICRO SIGN}m)", (2, 10)),
            ("X Tilt (\")",               (2, 10)),
            ("Y Tilt (\")",               (2, 10)),
            (u"X Trans (\N{MICRO SIGN}m)", (2, 10)),
            (u"Y Trans (\N{MICRO SIGN}m)", (2, 10)),
        )
        
        orientTitles, orientPrecWidthSet = list(zip(*orientColInfo))

        orientTitleWdgs = [RO.Wdg.StrLabel(self, text=label) for label in orientTitles]
        gr.gridWdg(
            label = "Orientation",
            dataWdg = orientTitleWdgs,
        )
        
        # data for orientation table layout: number of axes, label text, keyword prefix, help text
        orientNumLabelPrefixHelpList = (
            (NumPrimAxes, "Prim orient", "prim", "primary measured orientation"),
            (NumPrimAxes, "Prim des", "primDes", "primary desired orientation"),
            (NumSecAxes, "Sec orient", "sec", "secondary measured orientation"),
            (NumSecAxes, "Sec des", "secDes", "secondary desired orientation"),
        )

        # for each mirror, create a set of widgets find the associated keyvar
        for numAxes, niceName, keyPrefix, helpText in orientNumLabelPrefixHelpList:
            keyVarName = "%sOrient" % (keyPrefix,)
            orientWdgSet = [RO.Wdg.FloatLabel(
                    master = self,
                    precision = prec,
                    width = width,
                    helpText = "%s (%s)" % (helpText, keyVarName,),
                    helpURL = _HelpURL,
                ) for prec, width in orientPrecWidthSet[0:numAxes]
            ]
            gr.gridWdg (
                label = niceName,
                dataWdg = orientWdgSet
            )

            orientVar = getattr(tccModel, keyVarName)
            orientVar.addValueListCallback([wdg.set for wdg in orientWdgSet])

        # divider
        gr.gridWdg(
            label = False,
            dataWdg = Tkinter.Frame(self, height=1, bg="black"),
            colSpan = 10,
            sticky = "ew",
        )

        #
        # display mirror encoder data
        #

        statusLabelPrefixHelpList = (
            ("Prim state", "prim", "primary state"),
            ("Sec state", "sec", "secondary state"),
        )
        for niceName, keyPrefix, helpText in statusLabelPrefixHelpList:
            fullHelpText = "%s (%s)" % (helpText, keyVarName)
            keyVarName = "%sState" % (keyPrefix,)
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
                label = niceName,
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
                elif keyVar[1]:
                    stateStr = "%s: iter %s of %s" % (keyVar[0], keyVar[1], keyVar[2])
                else:
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

        # divider
        gr.gridWdg(
            label = False,
            dataWdg = Tkinter.Frame(self, height=1, bg="black"),
            colSpan = 10,
            sticky = "ew",
        )
        
        #
        # display mirror encoder data
        #

        # mount title
        axisTitles = ["%c (steps)" % (ii + ord("A"),) for ii in range(max(NumPrimAxes, NumSecAxes))]
        axisTitleWdgs = [RO.Wdg.StrLabel(self, text=label) for label in axisTitles]
        gr.gridWdg(
            label = "Mount",
            dataWdg = axisTitleWdgs,
        )

        # width
        mountWidth = 10

        # data for mount table layout: number of axes, label text, keyword prefix, help text
        mountNumLabelPrefixHelpList = (
            (NumPrimAxes, "Prim enc",     "primEnc", "primary measured encoder length"),
            (NumPrimAxes, "Prim des enc", "primDesEnc", "primary desired encoder length"),
            (NumPrimAxes, "Prim cmd",     "primCmd", "primary commanded actuator length"),
            (NumSecAxes,  "Sec enc",      "secEnc", "secondary measured encoder length"),
            (NumSecAxes,  "Sec des enc",  "secDesEnc", "secondary desired encoder length"),
            (NumSecAxes,  "Sec cmd",      "secCmd", "secondary commanded actuator length"),
        )
        
        # for each mirror, create a set of widgets and a key variable
        for numAxes, niceName, keyPrefix, helpText in mountNumLabelPrefixHelpList:
            keyVarName = "%sMount" % (keyPrefix,)
            mountWdgSet = [RO.Wdg.FloatLabel(self,
                    precision = 0,
                    width = mountWidth,
                    helpText = "%s (%s)" % (helpText, keyVarName),
                    helpURL = _HelpURL,
                ) for ii in range(numAxes)
            ]
            gr.gridWdg (
                label = niceName,
                dataWdg = mountWdgSet,
            )

            mountVar = getattr(tccModel, keyVarName)
            mountVar.addValueListCallback([wdg.set for wdg in mountWdgSet])

        self.statusWdg = TUI.Base.Wdg.StatusBar(self)
        gr.gridWdg(False, self.statusWdg, colSpan=10, sticky="ew")


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
