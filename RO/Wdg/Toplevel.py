#!/usr/local/bin/python
"""RO.Wdg.Toplevel wdigets are windows with some enhanced functionality, including:
- Remembers last position if closed or iconified
- Can record position and visiblity in a file

History:
2002-03-18 ROwen    First release.
2002-04-29 ROwen    Added "ToplevelSet".
2002-04-30 ROwen    Added wdgFunc argument to Toplevel.
2003-03-21 ROwen    Changed to allow resizable = True/False;
                    fixed a bug wherein geometry strings with +- or -+ were being rejected;
                    added Debug constant for more robust launching.
2003-03-25 ROwen    Added ability to create geom file if none exists
2003-06-18 ROwen    Modified to print at traceback and go on when the toplevel's widget
                    function fails; the test now excludes SystemExit and KeyboardInterrupt
2003-06-19 ROwen    Now saves window open/closed.
2003-11-18 ROwen    Modified to use SeqUtil instead of MathUtil.
2003-12-18 ROwen    Size is now saved and restored for windows with only one axis resizable.
                    Changed getGeometry to always return the entire geometry string.
2004-02-23 ROwen    Preference files are now read with universal newline support
                    on Python 2.3 or later.
2004-03-05 ROwen    Modified to use RO.OS.univOpen.
2004-05-18 ROwen    Bug fix in ToplevelSet: referred to defGeomFixDict instead of defGeomVisDict.
2004-07-16 ROwen    Modified Toplevel to propogate the exception if wdgFunc fails.
                    As a result, ToplevelSet.createToplevel no longer creates an erroneous
                    entry to a nonexistent toplevel if wdgFunc fails.
                    Bug fix: ToplevelSet could not handle toplevels that were destroyed.
                    Various methods modified to use getToplevel(name) to get the tl,
                    and if None is returned then the tl never existed or has been destroyed.
2004-08-11 ROwen    Renamed Close... constants to tl_Close...
                    Define __all__ to restrict import.
2005-06-08 ROwen    Changed ToplevelSet to a new-style class.
2005-10-18 ROwen    Fixed doc error: width, height ignored only if not resizable in that dir.
2006-04-26 ROwen    Added a patch (an extra call to update_idletasks) for a bug in Tcl/Tk 8.4.13
                    that caused certain toplevels to be displayed in the wrong place.
                    Removed a patch in makeVisible for an older tk bug; the patch
                    was now causing iconified toplevels to be left iconified.
                    Always pack the widget with expand="yes", fill="both";
                    this helps the user creates a window first and then makes it resizable.
                    Commented out code in makeVisible that supposedly avoids toplevels shifting;
                    I can't see how it can help.
"""
__all__ = ['tl_CloseDestroys', 'tl_CloseWithdraws', 'tl_CloseDisabled',
            'Toplevel', 'ToplevelSet']

import os.path
import re
import sys
import traceback
import Tkinter
import RO.CnvUtil
import RO.OS
import RO.SeqUtil

# constants for the closeMode argument
tl_CloseDestroys = 0
tl_CloseWithdraws = 1
tl_CloseDisabled = 2

# regular expressions for matching geometry strings
_GeomREStr = r"^=?(\d+x\d+)?([+-][+-]?\d+[+-][+-]?\d+)?$"
_GeomRE = re.compile(_GeomREStr, re.IGNORECASE)

# pack arguments as a function of (resazable in x, resizable in y)
#_PackArgsDict = {
#   (False, False): {"fill":"none", "expand":"no"},
#   (False, True):  {"fill":"y",    "expand":"yes"},
#   (True,  False): {"fill":"x",    "expand":"yes"},
#   (True,  True):  {"fill":"both", "expand":"yes"},
#}

class Toplevel(Tkinter.Toplevel):
    def __init__(self,
        master=None,
        geometry="",
        title=None,
        visible=True,
        resizable=True,
        closeMode=tl_CloseWithdraws,
        wdgFunc=None,       
    ):
        """Creates a new Toplevel. Inputs are:
        - master: master window; if omitted, root is used
        - geometry: Tk geometry string: WxH+-X+-Y;
          width and/or height are ignored if the window is not resizable in that direction
        - title: title of window
        - visible: display the window?
        - resizable: any of:
            - True (window can be resized)
            - False (window cannot be resized)
            - pair of bool: x, y dimension resizable by user?
        - closeMode: this is one of:
          - tl_CloseDestroys: close destroys the window and contents, as usual
          - tl_CloseWithdraws (default): close withdraws the window, but does not destroy it
          - tl_CloseDisabled: close does nothing
        - wdgFunc: a function which, when called with the toplevel as its only argument,
          creates a widget which is to be packed into the Toplevel.
          The widget is packed to grow as required based on resizable.
          
        Typically one uses RO.Alg.GenericCallback or something similar to generate wdgFunc,
        for example: GenericFunction(Tkinter.Label, text="this is a label").
        But BEWARE!!! if you use GenericCallback then you must give it NAMED ARGUMENTS ONLY.
        This is because GenericCallback puts unnamed saved (specified in advance) arguments first,
        but the master widget (which is passed in later) must be first.
        
        An alternative solution is to create a variant of GenericCallback that
        is specialized for Tk widgets or at least puts unnamed dynamic arguments first.
        """
        Tkinter.Toplevel.__init__(self, master)
        self.wm_withdraw()
        
        resizable = RO.SeqUtil.oneOrNAsList (resizable, 2, valDescr = "resizable")
        resizable = tuple([bool(rsz) for rsz in resizable])
        self.__canResize = resizable[0] or resizable[1]
        self.__geometry = ""
        self.__wdg = None  # contained widget, but only if wdgFunc specified

        if title:
            self.wm_title(title)
        self.wm_resizable(*resizable)
        
        self.bind("<Unmap>", self.__recordGeometry)
        self.bind("<Destroy>", self.__recordGeometry)
        
        # handle special close modes
        self.__closeMode = closeMode  # save in case someone wants to look it up
        if self.__closeMode == tl_CloseDisabled:
            def noop():
                pass
            self.protocol("WM_DELETE_WINDOW", noop)
        elif self.__closeMode == tl_CloseWithdraws:
            self.protocol("WM_DELETE_WINDOW", self.withdraw)
        
        # if a widget creation function supplied, use it
        if wdgFunc:
            try:
                self.__wdg = wdgFunc(self)
                #packArgs = _PackArgsDict.get(resizable, {})
                #self.__wdg.pack(**packArgs)            
                self.__wdg.pack(expand="yes", fill="both")
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                sys.stderr.write("Could not create window %r: %s\n" % (title, e))
                traceback.print_exc(file=sys.stderr)
                raise

        # Once window initial size is set, shrink-wrap behavior
        # goes away in both dimensions. If the window can only be
        # resized in one direction, the following bindings
        # restore shrink-wrap behavior in the other dimension.
        if self.__canResize:
            if not resizable[0]:
                # must explicitly keep width correct
                self.bind("<Configure>", self.__adjWidth)
            elif not resizable[1]:
                # must explicitly keep height correct
                self.bind("<Configure>", self.__adjHeight)

        # making the window visible after setting everything else up
        # works around several glitches:
        # - one of my windows was showing up in the wrong location, only on MacOS X aqua, for no obvious reason
        # - some windows with only one axis resizable were showing up with the wrong size
        #   (a well placed update_idletasks() also fixed that problem)
        if visible:
            # update_idletasks works around a bug in Tcl/Tk 8.4.13 that consistently caused
            # the Offset and Permissions windows to be drawn in the wrong place
            self.update_idletasks()
            self.__setGeometry(geometry)
            self.makeVisible()
        else:
            self.__setGeometry(geometry)
    
    def __sizePosFromGeom(self, geomStr):
        """Convenience function; splits a geometry string into its position
        and size components. Uses no knowledge of the state of the window.
        """
        match = _GeomRE.match(geomStr)
        if match == None:
            raise ValueError, "invalid geometry string %r" % (geomStr)
        return match.groups("")
    
    def __setGeometry(self, geomStr):
        """Set the geometry of the window based on a Tk geometry string.

        Similar to the standard geometry method, but records the new geometry
        and does not set the size if the window is not resizable.
        """
        #print "Toplevel.__setGeometry(%s)" % (geomStr,)
        sizeStr, posStr = self.__sizePosFromGeom(geomStr)
        if self.__canResize:
            #print "can resize: set geometry to %r" % (geomStr,)
            self.geometry(geomStr)
        else:
            #print "cannot resize: set geometry to %r" % (posStr,)
            self.geometry(posStr)
        if not self.getVisible():
            self.__geometry = geomStr
    
    def __recordGeometry(self, evt=None):
        """Record the current geometry of the window.
        """
        self.__geometry = self.geometry()
    
    def __adjWidth(self, evt=None):
        """Update geometry to shrink-to-fit width and user-requested height
        
        Use as the binding for <Configure> if resizable = (True, False).
        """
        height = self.winfo_height()
        reqwidth = self.winfo_reqwidth()
        if self.winfo_width() != reqwidth:
            self.geometry("%sx%s" % (reqwidth, height))
    
    def __adjHeight(self, evt=None):
        """Update geometry to shrink-to-fit height and user-requested width
        
        Use as the binding for <Configure> if resizable = (False, True).
        """
        reqheight = self.winfo_reqheight()
        width = self.winfo_width()
        if self.winfo_height() != reqheight:
            self.geometry("%sx%s" % (width, reqheight))
    
    def getVisible(self):
        """Returns True if the window is visible, False otherwise
        """
        return self.winfo_exists() and self.winfo_ismapped()
    
    def getGeometry(self):
        """Returns the geometry string of the window.
        
        Similar to the standard geometry method, but:
        - If the window is visible, the geometry is recorded as well as returned.
        - If the winow is not visible, the last recorded geometry is returned.
        - If the window was never displayed, returns the initial geometry
          specified, if any, else ""
        
        The position is measured in pixels from the upper-left-hand corner.
        """
        if self.getVisible():
            self.__recordGeometry()
        return self.__geometry
    
    def getWdg(self):
        """Returns the contained widget, if it was specified at creation with wdgFunc.
        Please use with caution; this is primarily intended for debugging.
        """
        return self.__wdg
    
    def makeVisible(self):
        """Displays the window, if withdrawn or deiconified, or raises it if already visible.
        """
        if self.wm_state() == "normal":
            # window is visible
            self.lift()  # note: the equivalent tk command is "raise"
        else:           
            # window is withdrawn or iconified
            # At one time I set the geometry first "to avoid displaying and then moving it"
            # but I can't remember why this was useful; meanwhile I've commented it out
#           self.__setGeometry(self.__geometry)
            self.wm_deiconify()
            self.lift()
    
    def __printInfo(self):
        """A debugging tool prints info to the main window"""
        print "info for RO.Wdg.Toplevel %s" % self.wm_title()
        print "getGeometry = %r" % (self.getGeometry(),)
        print "geometry = %r" % (self.geometry())
        print "width, height = %r, %r" % (self.winfo_width(), self.winfo_height())
        print "req width, req height = %r, %r" % (self.winfo_reqwidth(), self.winfo_reqheight())


class ToplevelSet(object):
    """A set of Toplevel windows that can record and restore positions to a file.
    """
    def __init__(self,
        fileName=None,
        defGeomVisDict=None,
        createFile=False,
    ):
        """Create a ToplevelSet
        Inputs:
        - fileName: full path to a file of geometry and visiblity info
            (see readGeomVisFile for file format);
            the file is read initially and the file name is the default for readGeomVisFile
        - defGeomVisDict: default geometry and visible info, as a dictionary
            whose keys are window names and values are tuples of:
            - Tk geometry strings: WxH+-X+-Y; None or "" for no default
            - visible flag; None for no default
        - createFile: if the geometry file does not exist,
            create a new blank one?
        """
        
        self.defFileName = fileName

        # geometry and visibility dictionaries
        # the file dictionaries contain data read from the geom/vis file
        # the default dictionaries contain programmer-supplied defaults
        # file data overrides programmer defaults
        # all dictionaries have name as the key
        # Geom dictionaries have a Tk geometry string as the value
        # Vis dictaraies have a boolean as the value
        self.fileGeomDict = {}
        self.fileVisDict = {}
        self.defGeomDict = {}
        self.defVisDict = {}
        if defGeomVisDict:
            for name, geomVis in defGeomVisDict.iteritems():
                geom, vis = geomVis
                if geom:
                    self.defGeomDict[name] = geom
                if vis:
                    self.defVisDict[name] = vis

        self.tlDict = {}    # dictionary of name:toplevel items
        if self.defFileName:
            self.readGeomVisFile(fileName, createFile)
    
    def addToplevel(self,
        toplevel,
        name,
    ):
        """Adds a new Toplevel instance to the set.
        """
        if self.getToplevel(name):
            raise RuntimeError, "toplevel %r already exists" % (name,)
        self.tlDict[name] = toplevel
    
    def createToplevel (self, 
        name,
        master=None,
        defGeom="",
        defVisible=None,
        **kargs):
        """Create a new Toplevel and add it to the set.
        
        Inputs are:
        - name: unique identifier for Toplevel.
            If you don't specify a separate title in kargs,
            the Toplevel's title is the last period-delimited field in name.
            This allows you to specify a category and a title, e.g. "Inst.Spicam".
        - defGeom: default Tk geometry string: WxH+-X+-Y;
            added to the default geometry dictionary
            (replacing the current entry, if any)
          width and height are ignored unless window is fully resizable
        - defVisible: default value for visible;
            added to the default visible dictionary
            (replacing the current entry, if any)
        - **kargs: keyword arguments for Toplevel, which see;
            note that visible is ignored unless defVisible is omitted
            and visible exists, in which case defVisible = visible
        
        Returns the new Toplevel
        """
        if self.getToplevel(name):
            raise RuntimeError, "toplevel %r already exists" % (name,)
        if defGeom:
            self.defGeomDict[name] = defGeom
        if defVisible == None:
            # if defVisible omitted, see if visible specified
            defVisible = kargs.get("visible", None)
        if defVisible != None:
            # if we have a default visibility, put it in the dictionary
            self.defVisDict[name] = bool(defVisible)
        geom = self.getDesGeom(name)
        kargs["visible"] = self.getDesVisible(name)
        if "title" not in kargs:
            kargs["title"] = name.split(".")[-1]
        #print "ToplevelSet is creating %r with master = %r, geom= %r, kargs = %r" % (name, master, geom, kargs)
        newToplevel = Toplevel(master, geom, **kargs)
        self.tlDict[name] = newToplevel
        return newToplevel
    
    def getDesGeom(self,
        name,
    ):
        """Returns the desired geometry for the named toplevel, or "" if none.
        
        The desired geometry is the entry in the geometry file (if any),
        else the entry in the default geometry dictionary.
        """
        return self.fileGeomDict.get(name, self.defGeomDict.get(name, ""))
    
    def getDesVisible(self,
        name,
    ):
        """Returns the desired visiblity for the named toplevel, or True if none.
        
        The desired visibility is the entry in the geom/vis file (if any),
        else the entry in the default visibility dictionary.
        """
        return self.fileVisDict.get(name, self.defVisDict.get(name, True))

    def getToplevel (self, name):
        """Returns the named Toplevel, or None of it does not exist.
        """
        tl = self.tlDict.get(name, None)
        if not tl:
            return None
        if not tl.winfo_exists():
            del self.tlDict[name]
            return None
        return tl
    
    def getNames (self, prefix=""):
        """Returns all window names that start with the specified prefix
        (or all names if prefix omitted). The names are in alphabetical order
        (though someday that may change to the order in which windows are added).
        
        The list includes toplevels that have been destroyed.
        """
        nameList = self.tlDict.keys()
        nameList.sort()
        if not prefix:
            return nameList
        return [name for name in nameList if name.startswith(prefix)]

    def makeVisible (self, name):
        tl = self.getToplevel(name)
        if not tl:
            raise RuntimeError, "No such window %r" % (name,)
        tl.makeVisible()
    
    def readGeomVisFile(self, fileName=None, doCreate=False):
        """Read toplevel geometry from a file.
        Inputs:
        - fileName: full path to file
        - doCreate: if file does not exist, create a blank one?
        
        File format:
        - Comments (starting with "#") and blank lines are ignored.
        - Data lines have the format:
          name = geometry, vis
          where:
          - geometry is a Tk geometry string (size info optional)
          - vis is optional
          - either value may be omitted to use the program default
          - if the second value is omitted then the comma is also optional
        """
        fileName = fileName or self.defFileName
        if not fileName:
            raise RuntimeError, "No geometry file specified and no default"
        
        if not os.path.isfile(fileName):
            if doCreate:
                try:
                    outFile = open(fileName, "w")
                    outFile.close()
                except StandardError, e:
                    sys.stderr.write ("Could not create geometry file %r; error: %s\n" % (fileName, e))
                sys.stderr.write ("Created blank geometry file %r\n" % (fileName,))
            else:
                sys.stderr.write ("Geometry file %r does not exist; using default values\n" % (fileName,))
            return

        try:
            inFile = RO.OS.openUniv(fileName)
        except StandardError, e:
            raise RuntimeError, "Could not open geometry file %r; error: %s\n" % (fileName, e)
            
        newGeomDict = {}
        newVisDict = {}
        try:
            for line in inFile:
                # if line starts with #, it is a comment, skip it
                if line.startswith("#"):
                    continue
                data = line.split("=", 1)
                if len(data) < 2:
                    # no data on this line; skip it
                    continue
                name = data[0].strip()
                if len(name) == 0:
                    continue

                geomVisList = data[1].split(",")
                if len(geomVisList) == 0:
                    continue

                geom = geomVisList[0].strip()
                if geom:
                    newGeomDict[name] = geom

                if len(geomVisList) > 1:
                    vis = geomVisList[1].strip()
                    if vis:
                        vis = RO.CnvUtil.asBool(vis)
                        newVisDict[name] = vis
            self.fileGeomDict = newGeomDict
            self.fileVisDict = newVisDict
        finally:
            inFile.close()
        
    def writeGeomVisFile(self, fileName=None, readFirst = True):
        """Writes toplevel geometry and visiblity info to a file
        that readGeomVisFile can read.
        Comments out entries for windows with default geometry and visibility,
        unless the data was specified in the file.
        
        Inputs:
        - fileName: full path name of geometry file
        - readFirst: read the geometry file first (if it exists) to be sure of having
          a current set of defaults (affects which entries will be commented out)
        """
        fileName = fileName or self.defFileName
        if not fileName:
            raise RuntimeError, "No geometry file specified and no default"
        
        if readFirst and os.path.isfile(fileName):
            self.readGeomVisFile(fileName)

        try:
            outFile = open(fileName, "w")
        except StandardError, e:
            raise RuntimeError, "Could not open geometry file %r; error: %s\n" % (fileName, e)
            
        try:
            names = self.getNames()
            names.sort()
            for name in names:
                defGeom = self.defGeomDict.get(name, "")
                defVis = self.defVisDict.get(name, None)
                
                tl = self.getToplevel(name)
                if tl:
                    currGeom = tl.getGeometry() or defGeom # since getGeometry returns "" if window never displayed
                    currVis = tl.getVisible()
                else:
                    currGeom = defGeom
                    currVis = False
                
                # record current values in file dictionary
                # (since we're about to update that)
                if (currGeom != defGeom):
                    self.fileGeomDict[name] = currGeom
                if (currVis != defVis):
                    self.fileVisDict[name] = currVis
                    
                # comment out entry if there is no entry in either file dictionary
                # (which can only be true if curr = def for geom and vis
                # and there was no entry in the file when it was last read)
                if self.fileGeomDict.has_key(name) or self.fileVisDict.has_key(name):
                    prefixStr = ""
                else:
                    prefixStr = "# "
                outFile.write("%s%s = %s, %s\n" % (prefixStr, name, currGeom, currVis))
        finally:
            outFile.close()


if __name__ == "__main__":
    from RO.Wdg.PythonTk import PythonTk
    root = PythonTk()
    
    testWin = Toplevel(
        title="test window",
        resizable=(False, True),
        geometry = "40x40+150+50"
    )
    l = Tkinter.Label(testWin, text="This is a label")
    l.pack()
    
    def printInfo():
        print "testWin.getGeometry = %r" % (testWin.getGeometry(),)
        print "geometry = %r" % (testWin.geometry())
        print "width, height = %r, %r" % (testWin.winfo_width(), testWin.winfo_height())
        print "req width, req height = %r, %r" % (testWin.winfo_reqwidth(), testWin.winfo_reqheight())
        print ""
    
    b = Tkinter.Button(root, text="Window Info", command=printInfo)
    b.pack()
            
    root.mainloop()
