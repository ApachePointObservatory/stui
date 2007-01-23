"""Run a file of commands.

Each line must consist of the actor followed by the command, e.g.:
tcc show time

Blank lines and lines beginning with # are ignored.

To do:
- Fix resizing
- Support Run Selection and Run From Cursor

Also, if these are easy to figure out:
- Clear CurrCmdTag if user edits the file
- Add appropriate accelerator keys for Save and Open

History:
2006-03-10 ROwen
"""
import os
import Tkinter
import RO.Wdg
import RO.CnvUtil
import tkFileDialog

HelpURL = "Scripts/BuiltInScripts/RunCommands.html"

CurrCmdTag = "currCmd"

class ScriptClass(object):
    def __init__(self, sr):
        self.filePath = None
    
        # make window resizable
        sr.master.winfo_toplevel().wm_resizable(True, True)
        
        # create widgets
        fileFrame = Tkinter.Frame(sr.master)
        fileMenubutton = Tkinter.Menubutton(
            fileFrame,
            text = "File",
            indicatoron = False,
            width = 4,
        )
        fileMenu = Tkinter.Menu(fileMenubutton,
            tearoff = False,
        )
        fileMenubutton["menu"] = fileMenu
        fileMenu.add_command(
            label="Open...",
            command = self.doOpen,
        )
        fileMenu.add_command(
            label = "Save",
            command = self.doSave,
        )
        fileMenu.add_command(
            label = "Save As",
            command = self.doSaveAs,
        )
        fileMenubutton.pack(side="left")
        
        self.filePathWdg = RO.Wdg.StrEntry(
            master = fileFrame,
            readOnly = True,
            helpText = "current file",
        )
        self.filePathWdg.pack(side="left", expand=True, fill="x")
        fileFrame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        yscroll = Tkinter.Scrollbar (
            master = sr.master,
            orient = "vertical",
        )
        self.textWdg = RO.Wdg.Text(
            sr.master,
            yscrollcommand = yscroll.set,
            width = 40,
            height = 10,
            #relief = "raised",
            #borderwidth = 1,
            helpText = "Commands to execute",
            helpURL = HelpURL,
        )
        
        # configure appearance of currently executing command
        self.textWdg.tag_configure(CurrCmdTag,
            relief = "raised",
            borderwidth = 1,
        )
#       yscroll.configure(command=self.textWdg.yview)
        self.textWdg.grid(row=1, column=0, sticky="nsew")
#       yscroll.grid(row=1, column=1, sticky="ns")
    
        sr.master.rowconfigure(1, weight=1)
        sr.master.columnconfigure(0, weight=1)
            
    def doOpen(self, wdg=None):
        filePath = tkFileDialog.askopenfilename(
    #       initialdir = None,
    #       initialfile = None,
            title = "File of commands",
        )
        if not filePath:
            return
    
        # handle case of filePath being a weird Tcl object
        self.filePath = RO.CnvUtil.asStr(filePath)
        
        fileObj = file(self.filePath, 'rU')
        try:
            fileData = fileObj.read()
            if fileData[-1] != "\n":
                fileData = fileData + "\n"
        finally:
            fileObj.close()
        
        self.textWdg.delete("0.0", "end")
        self.textWdg.insert("0.0", fileData)
        self.textWdg.see("0.0")
        
        self.filePathWdg.set(filePath)
        overflow = len(filePath) - self.filePathWdg["width"]
        if overflow > 0:
            self.filePathWdg.xview(overflow)
    
    def doSave(self):
        if not self.filePath:
            self.doSaveAs()
            return
        
        data = self.getData()
        outFile = file(self.filePath, 'w')
        try:
            outFile.write(data)
        finally:
            outFile.close()
    
    def doSaveAs(self):
        if self.filePath:
            currFileDir, currFileName = os.path.split(self.filePath)
        else:
            currFileDir = currFileName = None
        filePath = tkFileDialog.asksaveasfile(
            initialdir = currFileDir,
            initialfile = currFileName,
#           title = "File of commands",
        )
        if not filePath:
            return
        
        data = self.getData()
        outFile = file(filePath, "w")
        try:
            outFile.write(data)
        finally:
            outFile.close()
        self.filePath = filePath
    
    def getData(self):
        """Return the current text"""
        return self.textWdg.get("0.0", "end")
    
    def run(self, sr):
        self.textWdg.focus_get()
        textStr = self.getData()
        textList = textStr.split("\n")
        lineNum = 0
        for line in textList:
            lineNum += 1
            line = line.strip()
            if not line or line.startswith("#"):
                continue
        
            ind = "%d.0" % lineNum
            self.textWdg.tag_remove(CurrCmdTag, "0.0", "end")
            self.textWdg.tag_add(CurrCmdTag, ind, ind + " lineend")
            self.textWdg.see(ind)
            sr.showMsg("Executing: %s" % (line,))
            self.textWdg["state"] = "disabled"
            actor, cmdStr = line.split(None, 1)
            yield sr.waitCmd(
                actor = actor,
                cmdStr = cmdStr,
            )
    
    def end(self, sr):
        if not sr.isAborting():
            self.textWdg.tag_remove(CurrCmdTag, "0.0", "end")
        
        self.textWdg["state"] = "normal"
