#!/usr/local/bin/python
"""
A widget showing a set of options as checkbuttons.

To Do:
- Allow use of RO.InputCont.BoolOmitCont insted of BoolNegCont.

History:
2002-07-30 ROwen    Moved to the RO.Wdg module and renamed from OptionWdg.
2002-08-23 ROwen    Changed defIfDisabled to defIfHidden since Entry
    widgets still show values even if disabled (returning the default
    when a different value was visible would be a big mistake).
2002-11-15 ROwen    Enabled help, via the new ROCheckbutton.
2002-12-04 ROwen    Added support for help URLs for options;
    added helpText and helpURL support for default and clear buttons;
    bug fix: helpText was not optional for options.
2003-03-12 ROwen    Changed for ROCheckbutton->Checkbutton rename.
2003-03-14 ROwen    Changed to use InputCont modified BasicSetFmt.
2003-04-15 ROwen    Modified to use RO.Wdg.CtxMenu 2003-04-15;
                    removed clearHelpText, defHelpText.
2003-07-09 ROwen    Modified to use overhauled RO.InputCont.
2003-08-08 ROwen    Modified to track a change in RO.InputCont.
2004-05-18 ROwen    Eliminated negStr argument because it wasn't being used.
                    Stopped importing string, sys, RO.StringUtil and CtxMenu
                    since they weren't used.
2004-08-11 ROwen    Define __all__ to restrict import.
2004-09-14 ROwen    Modified to use helpURLPrefix as help url for header.
                    Bug fix: was incorrectly importing Button.
                    Bug fix: test code enable button was broken.
2004-12-13 ROwen    Renamed doEnable to setEnable for modified RO.InputCont.
2005-06-03 ROwen    Fixed one indentation quirk (space tab -> tab).
"""
__all__ = ['OptionButtons']

import RO.InputCont
import Button
import Checkbutton
import InputContFrame
import Label

class OptionButtons(InputContFrame.InputContFrame):
    def __init__ (self,
        master,
        name,
        optionList,
        helpURLPrefix=None,
        headerText=None,
        defButton=None,
        clearButton=None,
        omitDef = True,
        setDefIfAbsent = True,
        formatFunc = None,
        **kargs
    ):
        """Create a widget showing a set of options as checkboxes.

        Inputs:
        - name: name of option set;
            used as a namespace when multiple option sets are combined,
            and used as the name of the VMS qualifier, if relevant
        - optionList: data about the options.
            Each entry is a list of:
            - option name (used by getString)
            - option label text
            - default logical value
            - help text (optional)
            - help URL (optional)
        - helpURLPrefix: if supplied, every item in optionList
          will by default have a helpURL of _htlpURLPrefix + option name
          (but a specified help URL will override this for any individual entry).
          Also used as the help URL for the optional label.
        - headerText: text for an optional heading
        - defButton: controls whether there is a button to restore defaults; one of:
            - True: for a button entitled "Defaults"
            - False or None: no button
            - a string: text for the default button
        - clearButton: text for an optional "clear" button
            - if None, no button is supplied
            - if "", the button is entitled "Clear"
        - omitDef: if True: getValueDict returns {} if all values are default
            and getValueDict and getValueList omit individual values whose widgets are default
        - setDefIfAbsent: if True: setValueDict sets all widgets to their default value if name is absent
            and setValueDict and setValueList set individual widgets to their default value
            if they are missing from the value list.
        - formatFunc: the format function; takes one input, an RO.InputCont.BoolNegCont
            containing all of the option checkboxes, and returns a string
            The default format is RO.InputCont.BasicFmt.
        **kargs: keyword arguments for Frame
        """
        InputContFrame.InputContFrame.__init__(self, master, **kargs)

        # optional header
        if headerText:
            helpURL = helpURLPrefix
            if helpURL and helpURL.endswith("#"):
                helpURL = helpURL[:-1]
            Label.Label(
                master = self,
                text = headerText,
                helpURL = helpURL,
            ).pack(side="top", anchor="w")
        
        if formatFunc == None:
            formatFunc = RO.InputCont.BasicFmt()

        # create option checkboxes
        # and a list of input containers for them
        wdgNames = []
        wdgList = []
        for optionData in optionList:
            # the items in optionData are:
            # name, label, default value, helpURL, helpText
            # and the last two items are optional
            nameStr, labelStr, defVal = optionData[0:3]
            
            def listGet(aList, ind, defVal=None):
                try:
                    return aList[ind]
                except LookupError:
                    return defVal

            helpText = listGet(optionData, 3)
            helpURL = listGet(optionData, 4)
            if helpURLPrefix and not helpURL:
                helpURL = helpURLPrefix + nameStr
            wdg = Checkbutton.Checkbutton(self,
                text=labelStr,
                defValue = defVal,
                helpText = helpText,
                helpURL = helpURL,
            )
            wdg.pack(side="top", anchor="w")
            wdgList.append(wdg)
            wdgNames.append(nameStr)
        
        # create input container
        self.inputCont = (
            RO.InputCont.BoolNegCont (
                name = name,
                wdgs = wdgList,
                wdgNames = wdgNames,
                omitDef = omitDef,
                setDefIfAbsent = setDefIfAbsent,
                formatFunc = formatFunc,
            )
        )
    
        # optional extra buttons
        self.optWdgList = []

        # optional "restore defaults" button
        if defButton == True:
            defButton = "Defaults"
        if defButton not in (False, None):
            defButtonWdg = Button.Button(self,
                text=defButton,
                command=self.restoreDefault,
                helpText = "Restore defaults",
            )
            self.optWdgList.append(defButtonWdg)
        
        # optional "clear" button
        if clearButton == True:
            clearButton = "Clear"
        if clearButton not in (False, None):
            clearButtonWdg = Button.Button(self,
                text=clearButton,
                command=self.clear,
                helpText = "Uncheck all checkboxes",
            )
            self.optWdgList.append(clearButtonWdg)

        # pack optional buttons, if any
        for wdg in self.optWdgList:
            wdg.pack(side="top", anchor="nw")
    
if __name__ == "__main__":
    import PythonTk
    root = PythonTk.PythonTk()

    def doPrint():
        print "getString() = %r" % (optFrame.getString(),)
    
    def setEnable(wdg=None):
        optFrame.setEnable(enableButton.getBool())

    enableButton = Checkbutton.Checkbutton (
        master = root,
        defValue = True,
        callFunc = setEnable,
        text = "Enable",
    )
    enableButton.pack()

    printButton = Button.Button (
        master = root,
        command = doPrint,
        text = "Print Values",
    )
    printButton.pack()

    optFrame = OptionButtons(root,
        name = "OptionSet",
        optionList = (
            ("OptionA", "A", 1, "option a"),
            ("OptionB", "B", 0, "option b"),
            ("OptionC", "C", 1, "option c")
        ),
        headerText = "Options Wdg",
        defButton = True,
        clearButton = True,
        bg = "gray",
    )
    optFrame.pack()

    root.mainloop()
