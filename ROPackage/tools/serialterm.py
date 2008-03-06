#!/usr/bin/env python
"""Simple serial terminal.
Type and press <return> in the entry field along the bottom to send data
"""
import sys
import os
import Tkinter
RORoot = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), "python")
sys.path.append(RORoot)
import RO.CnvUtil
import RO.Comm.TkSerial
import RO.Wdg

class SerialTerminal(Tkinter.Frame):
    def __init__(self, master, portName, localEcho=False, **serialOptions):
        Tkinter.Frame.__init__(self, master)
        self.localEcho = RO.CnvUtil.asBool(localEcho)
        
        self.conn = RO.Comm.TkSerial.TkSerial(portName, readCallback=self.doRead, **serialOptions)
        self.logWdg = RO.Wdg.LogWdg(master)
        self.logWdg.grid(row=0, column=0, sticky="nsew")

        self.cmdWdg = RO.Wdg.CmdWdg(master, self.doWrite)
        self.cmdWdg.grid(row=1, column=0, sticky="ew")
        
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
    
    def doRead(self, conn):
        newData = self.conn.readLine()
        if not newData:
            return
        self.logWdg.addOutput(newData + "\n")
    
    def doWrite(self, strToSend):
        if self.localEcho:
            self.logWdg.addOutput(strToSend + "\n")
        self.conn.writeLine(strToSend)

if __name__ == "__main__":
    nArgs = len(sys.argv)
    if nArgs < 2 or (nArgs // 2) != (nArgs + 1) // 2:
        print """Usage: serialterm portname [opt1 val1 [opt2 val2 [...]]]

Options include:
baud: baud rate (default: 9600)
parity: (default: none)
dataBits: data bits (default: 8)
stopBits: stop bits (default: 1)
localEcho: True or False (default: False)
"""
        sys.exit(0)
    serialOptions = {}
    portName = sys.argv[1]
    for argInd in range(2, nArgs, 2):
        serialOptions[sys.argv[argInd]] = sys.argv[argInd+1]
    
    root = Tkinter.Tk()
    serTerm = SerialTerminal(root, portName, **serialOptions)
    root.mainloop()
    