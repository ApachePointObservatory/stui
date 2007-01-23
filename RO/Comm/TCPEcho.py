#!/usr/local/bin/python
"""A simple TCP echo server.
Based on the SocketServer example in Python Essential Reference.

Primarily intended to test other communication code.

History:
2004-07-09 ROwen
2007-01-03 ROwen    Fixed execution code.
"""
import SocketServer

class _EchoHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        f = self.request.makefile()
        for line in f:
            if line.strip() == "quit":
                break
            self.request.send(line)
        print "Closing echo server"
        f.close()

def startServer(port, multi=False):
    """Create server and start serving.
    
    Inputs:
    - port  TCP port
    - multi if True, serves multiple users,
            else just serves one user and quits
            when that user is done
    """
    serv = SocketServer.TCPServer(("", port), _EchoHandler)
    if multi:
        print "Starting multiple-user echo server on port", port
        print "Send 'quit' to end a connection"
        serv.serve_forever()
    else:
        print "Starting single-user echo server on port", port
        print "Send 'quit' to quit the server"
    
        serv.handle_request()

if __name__ == "__main__":
    startServer(2076)
