#!/usr/local/bin/python
"""HTTP download with Tkinter-based progress reporting

Downloads files given the url and destination path.
Reports progress and allows cancellation.

- The bottom state display label sometimes overlaps the details panel.
I've not found a solution. Using the setgrid option would help,
but only if the grid could be made an exact multiple of the line height
(tricky when the font size can change). Gridding the display panel first
does not help. I've considered using tags to insert the state information,
but there doesn't seem to be any way to set a tab stop in ens, ems
or "avarage width characters", just inches and other such units.
What's really wanted is a multi-column list widget. Saving that,
I think it best to live with the current cosmetic problem.
- Long file names will auto-scroll the list of files to the right;
it'd be best to force that back to the left. But I don't want
to do that if the user has scrolled, and I don't know how to
determine the current scroll position.

History:
2005-07-07 ROwen
2006-04-05 ROwen    Bug fix: _updDetailStatus failed if state was
                    aborting or aborted. 
"""
__all__ = ['HTTPGetWdg']

import os
import sys
import traceback
import weakref
import Bindings
import Tkinter
import RO.AddCallback
import RO.Constants
import RO.MathUtil
import RO.Comm.HTTPGet as HTTPGet
import RO.Wdg
import CtxMenu

_StatusInterval = 200 # ms between status checks

_DebugMem = False

class HTTPCallback(object):
    def __init__(self, httpGet, callFunc=None):
        object.__init__(self)
        self.callFunc = callFunc
        self.httpGet = httpGet
    
    def __call__(self):
        if self.httpGet == None:
            return
        
        if self.callFunc:
            try:
                self.callFunc(self.httpGet)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                errMsg = "httpGet callback %r failed: %s" % (self.callFunc, e)
                sys.stderr.write(errMsg + "\n")
                traceback.print_exc(file=sys.stderr)
        
        if self.httpGet.isDone():
            self.clear()

    def clear(self):
        """Clear the callback"""
        if _DebugMem:
            print "HTTPCallback(%s) clear" % (self.httpGet,)
        self.httpGet = None
        self.callFunc = None
    

class HTTPGetWdg(Tkinter.Frame):
    """A widget to initiate file get via http, to display the status
    of the transfer and to allow users to abort the transfer.
    
    Inputs:
    - master: master widget
    - maxTransfers: maximum number of simultaneous transfers; additional transfers are queued
    - maxLines: the maximum number of lines to display in the log window. Extra lines are removed (unless a queued or running transfer would be removed).
    - helpURL: the URL of a help page; it may include anchors for:
      - "LogDisplay" for the log display area
      - "From" for the From field of the details display
      - "To" for the To field of the details display
      - "State" for the State field of the details display
      - "Abort" for the abort button in the details display
    """
    def __init__(self,
        master,
        maxTransfers = 1,
        maxLines = 500,
        helpURL = None,
    **kargs):
        Tkinter.Frame.__init__(self, master = master, **kargs)
        self._memDebugDict = {}
        
        self.maxLines = maxLines
        self.maxTransfers = maxTransfers
        self.selHTTPGet = None # selected getter, for displaying details; None if none
        
        self.dispList = []  # list of displayed httpGets
        self.getQueue = []  # list of unfinished (httpGet, stateLabel) tuples
        
        self.yscroll = Tkinter.Scrollbar (
            master = self,
            orient = "vertical",
        )
        self.text = Tkinter.Text (
            master = self,
            yscrollcommand = self.yscroll.set,
            wrap = "none",
            tabs = (8,),
            height = 4,
            width = 50,
        )
        self.yscroll.configure(command=self.text.yview)
        self.text.grid(row=0, column=0, sticky="nsew")
        self.yscroll.grid(row=0, column=1, sticky="ns")
        Bindings.makeReadOnly(self.text)
        if helpURL:
            CtxMenu.addCtxMenu(
                wdg = self.text,
                helpURL = helpURL + "#LogDisplay",
            )
        
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        detFrame = Tkinter.Frame(self)
            
        gr = RO.Wdg.Gridder(detFrame, sticky="ew")
        
        self.fromWdg = RO.Wdg.StrEntry(
            master = detFrame,
            readOnly = True,
            helpURL = helpURL and helpURL + "#From",
            borderwidth = 0,
        )
        gr.gridWdg("From", self.fromWdg, colSpan=3)

        self.toWdg = RO.Wdg.StrEntry(
            master = detFrame,
            readOnly = True,
            helpURL = helpURL and helpURL + "#To",
            borderwidth = 0,
        )
        gr.gridWdg("To", self.toWdg, colSpan=2)
        
        self.stateWdg = RO.Wdg.StrEntry(
            master = detFrame,
            readOnly = True,
            helpURL = helpURL and helpURL + "#State",
            borderwidth = 0,
        )
        self.abortWdg = RO.Wdg.Button(
            master = detFrame,
            text = "Abort",
            command = self._abort,
            helpURL = helpURL and helpURL + "#Abort",
        )
        gr.gridWdg("State", self.stateWdg, colSpan=2)
        
        self.abortWdg.grid(row=1, column=2, rowspan=2, sticky="s")
        
        detFrame.columnconfigure(1, weight=1)
        
        detFrame.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        self.text.bind("<Button-1>", self._selectEvt)
        self.text.bind("<B1-Motion>", self._selectEvt)
        
        self._startNew()

    def getFile(self, *args, **kargs):
        """Get a file
    
        Inputs: the same as for RO.Comm.HTTPGet
        """
        httpGet = HTTPGet.HTTPGet(*args, **kargs)
        stateLabel = RO.Wdg.StrLabel(self, anchor="w", width=httpGet.StateStrMaxLen)
        self._trackMem(httpGet, str(httpGet))

        # display item and append to list
        # (in that order so we can test for an empty list before displaying)
        if self.dispList:
            # at least one item is shown
            self.text.insert("end", "\n")
            doAutoSelect = self.selHTTPGet in (self.dispList[-1], None)
        else:
            doAutoSelect = True
        self.text.window_create("end", window=stateLabel)
        self.text.insert("end", httpGet.dispStr)
        self.dispList.append(httpGet)

        # append httpGet to the queue
        self.getQueue.append((httpGet, stateLabel))

        httpGet.addCallback(
            RO.Alg.GenericCallback(self._stateCallback, stateLabel),
            callNow = True,
        )
        
        # purge old display items if necessary
        ind = 0
        selInd = None
        while max(self.maxLines, ind) < len(self.dispList):
            #print "HTTPGetWdg.getFile: maxLines=%s, ind=%s, nEntries=%s" % (self.maxLines, ind, len(self.dispList),)

            # only erase entries for files that are finished
            if not self.dispList[ind].isDone():
                #print "HTTPGetWdg.getFile: file at ind=%s is not done" % (ind,)
                ind += 1
                continue
            #print "HTTPGetWdg.getFile: purging entry at ind=%s" % (ind,)
            
            if (not doAutoSelect) and (self.selHTTPGet == self.dispList[ind]):
                selInd = ind
                #print "HTTPGetWdg.getFile: purging currently selected file; saving index"

            del(self.dispList[ind])
            self.text.delete("%d.0" % (ind+1,), "%d.0" % (ind+2,))

        # if one of the purged items was selected,
        # select the next down extant item
        # auto scroll
        if doAutoSelect:
            self._selectInd(-1)
            self.text.see("end")
        elif selInd != None:
            self._selectInd(selInd)
        
        #print "dispList=", self.dispList
        #print "getQueue=", self.getQueue

    
    def _abort(self):
        """Abort the currently selected transaction (if any).
        """
        if self.selHTTPGet:
            self.selHTTPGet.abort()
    
    def _selectEvt(self, evt):
        """Determine the line currently pointed to by the mouse
        and show details for that transaction.
        Intended to handle the mouseDown event.
        """
        self.text.tag_remove("sel", "1.0", "end")
        x, y = evt.x, evt.y
        mousePosStr = "@%d,%d" % (x, y)
        indStr = self.text.index(mousePosStr)
        ind = int(indStr.split(".")[0]) - 1
        self._selectInd(ind)
        return "break"
    
    def _selectInd(self, ind):
        """Display details for the httpGet at self.dispList[ind]
        and selects the associated line in the displayed list.
        If ind == None then displays no info and deselects all.
        """
        self.text.tag_remove('sel', '1.0', 'end')
        try:
            self.selHTTPGet = self.dispList[ind]
            if ind < 0:
                lineNum = len(self.dispList) + 1 + ind
            else:
                lineNum = ind + 1
            self.text.tag_add('sel', '%s.0' % lineNum, '%s.0 lineend' % lineNum)
        except IndexError:
            self.selHTTPGet = None
        self._updDetailStatus()
    
    def _startNew(self):
        """Start new transfers if any are pending and there is room
        """
        newGetQueue = list()
        nRunning = 0
        for httpGet, stateLabel in self.getQueue:
            if httpGet.isDone():
                continue

            newGetQueue.append((httpGet, stateLabel))
            state = httpGet.getState()
            if state == httpGet.Queued:
                if nRunning < self.maxTransfers:
                    httpGet.start()
                    nRunning += 1
            elif state in (httpGet.Running, httpGet.Connecting):
                nRunning += 1
        self.getQueue = newGetQueue
    
        #self._updDetailStatus()
        
    def _stateCallback(self, stateLabel, httpGet):
        """State callback for running transfers"""
        state = httpGet.getState()
        if state == httpGet.Running:
            readBytes, totBytes = httpGet.getBytes()
            
            if totBytes:
                pctDone = int(round(100 * readBytes / float(totBytes)))
                stateLabel["text"] = "%3d %%" % pctDone
            else:
                kbRead = readBytes / 1024
                stateLabel["text"] = "%d kB" % kbRead
        else:
            # display text description of state
            stateStr = httpGet.getStateStr(state)
            if state == httpGet.Failed:
                severity = RO.Constants.sevError
            elif state in (httpGet.Aborting, httpGet.Aborted):
                severity = RO.Constants.sevWarning
            else:
                severity = RO.Constants.sevNormal
            stateLabel.set(stateStr, severity=severity)
        
        if httpGet == self.selHTTPGet:
            self._updDetailStatus()
        
        if httpGet.isDone():
            self._startNew()

    def _trackMem(self, obj, objName):
        """Print a message when an object is deleted.
        """
        if not _DebugMem:
            return
        objID = id(obj)
        def refGone(ref=None, objID=objID, objName=objName):
            print "%s deleting %s" % (self.__class__.__name__, objName,)
            del(self._memDebugDict[objID])

        self._memDebugDict[objID] = weakref.ref(obj, refGone)
        del(obj)
    
    def _updDetailStatus(self):
        """Update the detail status for self.selHTTPGet"""
        if not self.selHTTPGet:
            self.fromWdg.set("")
            self.toWdg.set("")
            self.stateWdg.set("")
            if self.abortWdg.winfo_ismapped():
                self.abortWdg.grid_remove()
            return

        httpGet = self.selHTTPGet
        currState = httpGet.getState()
        
        # show or hide abort button, appropriately
        if currState >= httpGet.Running:
            if not self.abortWdg.winfo_ismapped():
                self.abortWdg.grid()
        else:
            if self.abortWdg.winfo_ismapped():
                self.abortWdg.grid_remove()

        severity = RO.Constants.sevNormal
        if currState == httpGet.Running:
            readBytes, totBytes = httpGet.getBytes()
            if totBytes:
                stateStr = "read %s of %s bytes" % (readBytes, totBytes)
            else:
                stateStr = "read %s bytes" % (readBytes,)
        elif currState == httpGet.Failed:
            stateStr = "Failed: %s" % (httpGet.getErrMsg())
            severity = RO.Constants.sevError
        else:
            stateStr = httpGet.getStateStr()
            if currState in (httpGet.Aborting, httpGet.Aborted):
                severity = RO.Constants.sevWarning

        self.stateWdg.set(stateStr, severity=severity)
        self.fromWdg.set(httpGet.dispStr)
        self.toWdg.set(httpGet.toPath)


if __name__ == "__main__":
    from PythonTk import *
    root = PythonTk()

    row = 0
    
    testFrame = HTTPGetWdg (
        master=root,
    )
    testFrame.grid(row=row, column=0, columnspan=2, sticky="nsew")
    row += 1

    overwriteVar = Tkinter.BooleanVar()
    overwriteVar.set(True)
    overwriteWdg = Tkinter.Checkbutton(
        master=root,
        text="Overwrite",
        variable=overwriteVar,
    )
    overwriteWdg.grid(row=row, column=1, sticky="w")
    row += 1

    Tkinter.Label(root, text="ToPath:").grid(row=row, column=0, sticky="e")
    toPathWdg = Tkinter.Entry(root)
    toPathWdg.insert(0, "tempfile")
    toPathWdg.grid(row=row, column=1, sticky="ew")
    row += 1
    
    Tkinter.Label(root, text="FromURL:").grid(row=row, column=0, sticky="e")
    fromURLWdg = Tkinter.Entry(root)
    fromURLWdg.grid(row=row, column=1, sticky="ew")
    row += 1

    
    def getFile(evt):
        overwrite = overwriteVar.get()
        toPath = toPathWdg.get()
        fromURL = fromURLWdg.get()
        testFrame.getFile(url=fromURL, toPath=toPath, overwrite=overwrite)
        
    fromURLWdg.bind("<Return>", getFile)
    
    root.rowconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)

    root.mainloop()
