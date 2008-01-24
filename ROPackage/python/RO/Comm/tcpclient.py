"""Example trivial telnet client using TkSocket"""
import sys
import Tkinter
import TCPConnection
import RO.Wdg

class TCPClient(Tkinter.Frame):
    def __init__(self, master, addr, port=None):
        Tkinter.Frame.__init__(self, master)
        self.logWdg = RO.Wdg.LogWdg(
            master = self,
            maxLines = 1000,
        )
        self.logWdg.grid(row=0, column=0, sticky="nsew")
#        self.logWdg.pack(side="top", expand=True, fill="both")
        
        self.cmdWdg = RO.Wdg.CmdWdg(
            master = self,
            maxCmds = 100,
            cmdFunc = self.doCmd,
        )
        self.cmdWdg.grid(row=1, column=0, sticky="ew")
#        self.cmdWdg.pack(side="top", expand=True, fill="x")
        
        self.conn = TCPConnection.TCPConnection(
            host = addr,
            port = port,
            readLines = True,
            stateCallback = self.connState,
            readCallback = self.connRead,
        )
        self.conn.connect()
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def connState(self, sock):
        stateVal, stateStr, reason = sock.getFullState()
        if reason:
            self.logMsg("*** Socket %s: %s" % (stateStr, reason))
        else:
            self.logMsg("*** Socket %s" % (stateStr,))
    
    def connRead(self, sock, readStr):
        self.logMsg(repr(readStr))

    def doCmd(self, cmd):
        if not self.conn.isConnected():
            self.logMsg("*** Not connected")
        self.conn.writeLine(cmd)
    
    def logMsg(self, msg):
        """Append msg to log, with terminating \n"""
        self.logWdg.addOutput(msg + "\n")


if __name__ == "__main__":
    if len(sys.argv) not in (2,3):
        print "Usage: tcpclient.py addr [port]"
        sys.exit(1)
    
    addr = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else 23
    
    root = Tkinter.Tk()
    root.geometry("400x200")
    client = TCPClient(root, addr, port)
    client.pack(side="top", expand=True, fill="both")

    root.mainloop()