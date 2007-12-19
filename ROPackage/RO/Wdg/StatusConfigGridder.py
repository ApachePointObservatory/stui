#!/usr/bin/env python
"""Tools for gridding widgets

History:
2003-05-06 ROwen    Adapted from ChangedGridder.
2004-05-18 ROwen    Modified _StatusConfigGridSet._makeChangedWdg
                    to eliminate two unused args (colSpan and sticky).
2004-08-11 ROwen    Renamed StatusConfigGridSet->_StatusConfigGridSet.
                    Define __all__ to restrict import.
2004-09-14 ROwen    Stopped importing RO.Wdg to avoid circular imports.
2004-11-29 ROwen    Modified to include ConfigCat as a class constant.
2005-01-05 ROwen    Got rid of the changed widget; use autoIsCurrent mode
                    in RO.Wdg widgets to indicate "changed", instead.
2005-05-26 ROwen    Bug fix: gridWdg mis-set nextCol if cfgWdg False or None.
                    Improved error message for units and cfgUnits being the same widget.
2006-04-27 ROwen    Removed ignored clearMenu and defMenu arguments (thanks pychecker!).
2006-10-31 ROwen    Added support adding help text and URL to created widgets.
                    Modified for changed Gridder._BaseGridSet.
2007-12-19 ROwen    Added numStatusCols argument. This makes it easier to start all configuration widgets
                    in the same column.
"""
__all__ = ['StatusConfigGridder']

import Tkinter
import RO.MathUtil
import Gridder

ConfigCat = "config"

class StatusConfigGridder(Gridder.Gridder):
    ConfigCat = ConfigCat
    def __init__(self,
        master,
        row = 0,
        col = 0,
        sticky = "e",
        statusCols = 2,
        numStatusCols = None,
    ):
        """Create an object that grids a set of status and configuration widgets.
        
        Inputs:
        - master        Master widget into which to grid
        - row           Starting row
        - col           Starting column
        - sticky        Default sticky setting for the status and config widgets
        - numStatusCols default number of columns for status widgets (including units but not label);
                        if None then the first configuration widget is gridded in the next column after
                        the last status widget.
                        You may wish to specify more columns than required; it is almost always harmless
                        and your code will still work if you add status widgets that use more columns.
                        
        """
        Gridder.Gridder.__init__(self,
            master = master,
            row = row,
            col = col,
            sticky = sticky,
        )
        if numStatusCols != None:
            numStatusCols = int(numStatusCols)
        self._numStatusCols = numStatusCols
    
    def gridWdg(self,
        label = None,
        dataWdg = None,
        units = None,
        cfgWdg = None,
        cat = None,
    **kargs):
        """Grids (in order)
        - labelWdg: a label widget
        - dataWdg: one or more status widgets
        - unitsWdg: units
        (the following are all None if cfgWdg not specified):
        - cfgWdg: one or more config widgets
        - cfgUnitsWdg: a config units label
        
        Configuration widgets are automatically added
        to the show/hide set ConfigCat and so are hidded by default.
        To display them you must call showHideWdg(config=True)
        
        Warning: a widget cannot be gridded twice, so:
        - Units cannot be an actual widget; it must be a string
          or variable (or None)
        - There should be no common widgets in dataWdg or cfgWdg

        Returns a _StatusConfigGridSet object that allows easy access
        to the various widgets and related information.
        Increments row.next.
        """
        basicArgs = self._basicKArgs(**kargs)
        basicArgs.setdefault("numStatusCols", self._numStatusCols)
        gs = _StatusConfigGridSet(
            master = self._master,
            label = label,
            dataWdg = dataWdg,
            cfgWdg = cfgWdg,
            units = units,
        **basicArgs)
        self._nextRow = gs.row + 1
        self._nextCol = max(gs.nextCol, self._nextCol)

        if cat != None:
            self.addShowHideWdg(cat, gs.wdgSet)
        
        # set show/hide category ConfigCat for configuration widgets
        if cfgWdg:
            self.addShowHideWdg(ConfigCat, gs.cfgWdg)
            self.addShowHideWdg(ConfigCat, gs.cfgUnitsWdg)

        return gs


class _StatusConfigGridSet(Gridder._BaseGridSet):
    def __init__ (self,
        master,
        label = None,
        dataWdg = None,
        units = None,
        cfgWdg = None,
        cfgUnits = None,
        row = 0,
        col = 0,
        colSpan = 1,
        cfgColSpan = None,
        sticky = "e",
        cfgSticky = None,
        numStatusCols = None,
        helpText = None,
        helpURL = None,
    ):
        """Creates and grids (in order) the following attributes:
        - labelWdg: a label widget
        - dataWdg: one or more status widgets
        - unitsWdg: units
        (the following are all None if cfgWdg not specified):
        - cfgWdg: one or more config widgets
        - cfgUnitsWdg: a config units label
        
        Inputs:
        - label         label text, variable, widget, None, False or "" (see Notes)
        - dataWdg       the status widgets: a widget or sequence of widgets,
                        each of which can be None or False (see Notes)
        - units         status units text, variable, widget, None, False or "" (see Notes)
        - cfgWdg        one or more configuration widgets (same rules as dataWdg)
        - cfgUnits      units for the config widget; defaults to units (but see Error Conditions below);
                        ignored if cfgWdg is None or True
        - cat           one or more show/hide categories; if specified then all widgets are added
                        to the show/hide list using these categories
        - row           row in which to grid; -1 means the same row as last time; default is the next row
        - col           column at which to start gridding; default is the default column
        - colSpan       column span for each of the data (status) widgets
        - cfgColSpan    column span for each of the config widgets; defaults to colSpan
        - sticky        sticky option for the status widgets
        - cfgSticky     sticky option for the config widgets; defaults to sticky
        - numStatusCols number of columns for status widgets (including units but not label);
                        if None then the first configuration widget is gridded in the next column after
                        the last status widget.
        - helpText      help text for any created widgets; if True then copied from the first dataWdg
        - helpURL       help URL for any created widgets; if True then copied from the first dataWdg

        Error Conditions:
        - Raise ValueError if units and cfgUnits are the same widget (but only if cfgWdg is
          not None or False, because otherwise cfgUnits is ignored).
          This is because a widget cannot be gridded in two places.
        - Raise RuntimeError if numStatusCols is not None and you use more than numStatusCols columns
          for status widgets

        Notes:
        - If a widget is None or False then nothing is gridded or added to gs.wdgSet for that widget,
          but space is handled differently in the two cases:
          - If a widget is None then the appropriate number of empty columns are used for it
          - If a widget is False then no columns are used for it
        - If a label or units widget is "" then an empty RO.Wdg.StrLabel is gridded (which you can then
          set as you desire).
        """
        if cfgColSpan == None:
            cfgColSpan = colSpan
        if cfgUnits == None:
            cfgUnits = units
        if cfgSticky == None:
            cfgSticky = sticky
        if numStatusCols != None:
            numStatusCols = int(numStatusCols)

        Gridder._BaseGridSet.__init__(self,
            master,
            row,
            col,
            helpText = helpText,
            helpURL = helpURL,
        )

        self._numStatusCols = numStatusCols

        self._setHelpFromDataWdg(dataWdg)
        
        self.labelWdg = self._makeWdg(label)
        self._gridWdg(self.labelWdg, sticky="e", colSpan=1)

        self.dataWdg = dataWdg
        self._gridWdg(self.dataWdg, sticky=sticky, colSpan=colSpan)
        
        self.unitsWdg = self._makeWdg(units)
        self._gridWdg(self.unitsWdg, sticky="w", colSpan=1)
        
        if self._numStatusCols != None:
            cfgStartCol = self.begCol + 1 + self._numStatusCols # 1 for label
            overflowCols = self.nextCol - cfgStartCol
            if overflowCols > 0:
                raise RuntimeError("Too many status widgets; numStatusCols=%s; num used=%s" %
                    (self._numStatusCols, self._numStatusCols + overflowCols))
            self.nextCol = cfgStartCol
        
        if cfgWdg:
            self.cfgWdg = cfgWdg
            self._gridWdg(self.cfgWdg, sticky=cfgSticky, colSpan=cfgColSpan)
            
            self.cfgUnitsWdg = self._makeWdg(cfgUnits)
            if self.cfgUnitsWdg and self.cfgUnitsWdg == self.unitsWdg:
                raise ValueError, "units is a widget, so cfgUnits must be specified and must be a different widget"
            self._gridWdg(self.cfgUnitsWdg, sticky="w", colSpan=1)
        else:
            self.cfgWdg = None
            self.cfgUnitsWdg = None
            if cfgWdg != False:     
                self.nextCol += cfgColSpan
            if cfgUnits != False:
                self.nextCol += 1