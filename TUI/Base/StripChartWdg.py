"""A specialization of RO.Wdg.StripChart that adds methods to trace keyVars

History:
2010-10-01 ROwen
"""
import RO.Wdg.StripChartWdg

TimeConverter = RO.Wdg.StripChartWdg.TimeConverter

class StripChartWdg(RO.Wdg.StripChartWdg.StripChartWdg):
    def plotKeyVar(self, name, subplotInd, keyVar, keyInd=0, scale=1.0, **kargs):
        """Plot one value of one keyVar
        
        Inputs:
        - name: name of plot line (must be unique on the strip chart)
        - subplotInd: index of line on Subplot
        - keyVar: keyword variable to plot
        - keyInd: index of keyword variable to plot
        - scale: plotted value = keyVar[keyInd] * scaleFac
        **kargs: keyword arguments for StripChartWdg.addLine
        """
        self.addLine(name, subplotInd=subplotInd, **kargs)
        
        def callFunc(keyVar, name=name, keyInd=keyInd, scale=float(scale)):
            if not keyVar.isCurrent or not keyVar.isGenuine:
                return
            val = keyVar[keyInd]
            if val == None:
                return
            self.addPoint(name, val * scale)
        
        keyVar.addCallback(callFunc, callNow=False)
