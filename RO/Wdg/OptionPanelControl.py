#!/usr/bin/env python
"""
A set of checkbuttons that hides or shows widgets, e.g. option setting panels.

If a widget has a method getShowVar that returns a Tkinter.BooleanVar,
then that widget can control its own showing or hiding by
setting the variable True or False, respectively.

History:
2002-07-30 ROwen    Moved into the RO.Wdg module and renamed from OptionButtonWdg.
2002-08-02 ROwen    Added takefocus argument.
2003-03-12 ROwen    Changed for ROCheckbutton->Checkbutton rename.
2003-04-18 ROwen    Changed from checkboxes to raised/sunken buttons.
2003-05-29 ROwen    Added support for help text and help URLs.
2003-11-04 ROwen    Added support for getShowVar in the displayed widgets.
2004-05-18 ROwen    Bug fix: helpURL was being ignored.
                    Removed double import of Checkbutton.
2004-08-11 ROwen    Define __all__ to restrict import.
2005-06-02 ROwen    Modified to use RO.Wdg.Checkbutton's default padding
                    (which is platform-specific to work around cosmetic problems).
"""
__all__ = ['OptionPanelControl']

import Tkinter
import RO.Alg
from Checkbutton import Checkbutton
from CtxMenu import CtxMenuMixin

class _WdgButton(Checkbutton):
    """A checkbutton that shows or hides a gridded widget.

    Subtleties:
    - If the widget has a method getShowVar that returns a Tkinter.BooleanVar,
    then the widget can also control its own hiding by toggling the variable.
    - If this button is disabled then the widget is hidden.
    """
    def __init__(self,
        master,
        wdg,
        wdgName,
        helpText = None,
        helpURL = None,
        takefocus = True,
    ):
        self.__wdg = wdg
        
        try:
            var = wdg.getShowVar()
        except AttributeError:
            var = Tkinter.BooleanVar()
        
        Checkbutton.__init__(self,
            master = master,
            text = wdgName,
            helpText = helpText,
            helpURL = helpURL,
            takefocus = takefocus,
            indicatoron = False,
            var = var,
            callFunc = self.doClick,
        )
    
    def doClick(self, btn=None):
        """Handle a change in checkbutton state
        by showing or hiding the widget appropriately.
        """
        if self.getBool() and self.getEnable():
            self.__wdg.grid()
        else:
            self.__wdg.grid_remove()

    def setEnable(self, doEnable):
        """Enable or disable the checkbutton.
        If disabled then the associated widget is hidden,
        else it is shown or hidden according to the checkbutton
        """
        Checkbutton.setEnable(self, doEnable)
        self.doClick()


class OptionPanelControl(Tkinter.Frame, CtxMenuMixin):
    def __init__ (self,
        master,
        wdgList,
        labelText=None,
        takefocus=True,  # should the checkboxes take focus?
    **kargs):
        """
        Inputs:
        - wdgList   a list of data about the widgets to show or hide;
            each data is a list of 2-4 elements containing:
            - text for checkbox control
            - the widget itself
            - help text (optional)
            - help URL (optional)
        - labelText text for a label above the set of checkbuttons
        - takefocus should the checkbuttons take focus?
        - **kargs   keyword arguments for Tkinter.Frame
        
        All widgets in wdgList must have a common master, which the user
        is responsible for displaying (i.e. packing or gridding).
        This widget displays checkbuttons which will automatically
        show or hide (by gridding or ungridding) the widgets
        within their master frame.
        """
        Tkinter.Frame.__init__(self, master, **kargs)
        CtxMenuMixin.__init__(self)
        self._btnDict = {}
        
        if labelText != None:
            Tkinter.Label(self, text=labelText).pack(side="top", anchor="nw")

        wdgMaster = wdgList[0][1].master
        emptyFrame = Tkinter.Frame(wdgMaster)
        emptyFrame.grid(row=0, column=0)
        self.update_idletasks()
        
        
        for ind in range(len(wdgList)):
            wdgData = wdgList[ind]
            wdgName = wdgData[0]
            wdg = wdgData[1]

            try:
                helpText = wdgData[2]
            except IndexError:
                helpText = "show/hide %s panel" % wdgName
                
            try:
                helpURL = wdgData[3]
            except IndexError:
                helpURL = None
                
            wdg.grid(row=0, column=ind, sticky="n")
            wdg.grid_remove()

            # create the checkbutton to control hiding of the widget
            btn = _WdgButton(
                master = self,
                wdg = wdg,
                wdgName = wdgName,
                helpText = helpText,
                helpURL = helpURL,
                takefocus = takefocus,
            )
            btn.pack(side="top", anchor="nw")
            
            self._btnDict[wdgName] = btn
    
    def setEnable(self, wdgName, doEnable):
        """Enables or disables the appropriate widget control button.
        If disabled, then the associated widget is hidden,
        else it is either shown or hidden according to the button.
        
        Raises KeyError if no such widget.
        """
        self._btnDict[wdgName].setEnable(doEnable)
    

if __name__ == "__main__":
    from RO.Wdg.PythonTk import PythonTk
    root = PythonTk()
    
    # frame for the set of hideable widgets
    wdgFrame = Tkinter.Frame(root, bg="red", relief="ridge")
    
    # hideable widgets
    wdgA = Tkinter.Label(wdgFrame, text="Wdg A")
    wdgB = Tkinter.Label(wdgFrame, text="Wdg B")
    wdgC = Tkinter.Label(wdgFrame, text="Wdg C")
    
    extFrame = OptionPanelControl(
        root,
        wdgList = (
            ("Wdg A", wdgA),
            ("Wdg B", wdgB),
            ("Wdg C", wdgC),
        ),
        labelText="Show/Hide:",
    )
    extFrame.pack(side="left")
    
    wdgFrame.pack(side="left")

    root.mainloop()
