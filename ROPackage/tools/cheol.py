#!/usr/bin/env python

"""
cheol:  change end of line character
Copyright (C) 2000-2001 Gordon Worley

This program is free software; you can redistribute it and/or modify
it under the terms of the Python License, version 2.1.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
Python License, version 2.1 for more details.

For a copy of the Python License, version 2.1, visit
<http://www.python.org/>.

To contact me, please visit my Web site at <http://homepage.mac.com/
redbird/> or e-mail me at <redbird@rbisland.cx>.

#history

0.5.2 - added --version command
0.5.1 - added support for long (--) options
0.5 - added support for following links and verbosity.  Lot of work.
0.3.5 - removed pattern matching since not unixy
0.3 - added help and ability to convert to mac and dos.  Name changed
      to cheol.py from unixify.pl.
0.1 - added recursion, uses Jurgen Hermann's FileMorpher
0.0 - just converts the given files
"""

__version__ = "cheol 0.5.2, Copyright 2000-2001 Gordon Worley via the Python License, version 2.1.\nType -h for help"
#fn = filename

#this first part is not by me, but put right in this code
#so that everything can stay in one file :-)
#by Jurgen Hermann, from Python Cookbook (ASPN)

import os, string 
 
def replaceFile(oldname, newname): 
    """ Rename file 'oldname' to 'newname'. 
    """ 
    if os.name == 'nt' and os.path.exists(oldname): 
        # POSIX rename does an atomic replace, WIN32 rename does not. :-( 
        try: 
            os.remove(newname) 
        except OSError, exc: 
            import errno 
            if exc.errno != errno.ENOENT: raise exc 
 
    # rename it 
    os.rename(oldname, newname) 
 
 
class FileMorpher: 
    """ A class that enables a client to securely update an existing file, 
        including the ability to make an automated backup version. 
    """ 
 
    def __init__(self, filename, **kw): 
        """ The constructor takes the filename and some options. 
 
            backup -- boolean indicating whether you want a backup file

                (default is yes) 
        """ 
        self.filename = filename 
        self.do_backup = kw.get('backup', 0) 
 
        self.stream = None 
        self.basename, ext = os.path.splitext(self.filename) 
 
 
    def __del__(self): 
        if self.stream: 
            # Remove open temp file 
            self.__close() 
            os.remove(self.__tempfile()) 
 
 
    def __tempfile(self): 
        return self.basename + ".tmp" 
 
 
    def __close(self): 
        """ Close temp stream, if open. 
        """ 
        if self.stream: 
            self.stream.close() 
            self.stream = None 
 
 
    def load(self): 
        """ Load the content of the original file into a string and 
            return it. All I/O exceptions are passed through. 
        """ 
        file = open(self.filename, "rt") 
        try: 
            content = file.read() 
        finally: 
            file.close() 
 
        return content 
 
 
    def save(self, content): 
        """ Save new content, using a temporary file. 
        """ 
        file = self.opentemp() 
        file.write(content) 
        self.commit() 
 
 
    def opentemp(self): 
        """ Open a temporary file for writing and return an open stream. 
        """ 
        assert not self.stream, "Write stream already open" 
 
        self.stream = open(self.__tempfile(), "wt") 
 
        return self.stream         
 
 
    def commit(self): 
        """ Close the open temp stream and replace the original file, 
            optionally making a backup copy. 
        """ 
        assert self.stream, "Write stream not open" 
 
        # close temp file 
        self.__close() 
 
        # do optional backup and rename temp file to the correct name 
        if self.do_backup: 
            replaceFile(self.filename, self.basename + ".bak") 
        replaceFile(self.__tempfile(), self.filename) 

#end part not by me
#begin part by me

def convert(fn, mode, is_recv, follow_links, verbose):
    if is_recv:
        if os.path.isdir(fn) and not os.path.islink(fn):
            if verbose:
                print "%s/:" % fn
            os.chdir(fn)
            fns = os.listdir("./")
            for afn in fns:
                convert(afn, mode, is_recv, follow_links, verbose)
            os.chdir("..")
            if verbose:
                print "../:"
        elif os.path.isdir(fn) and os.path.islink(fn) and os.path.islink(fn) <= follow_links:
            jfn = os.readlink(fn)
            if verbose:
                print "%s/ (%s/):" % (fn, jfn)
            fns = os.listdir(fn)
            for afn in fns:
                convert(os.path.join(jfn, afn), mode, is_recv, follow_links, verbose)
            if verbose:
                print "../:"
    if not os.path.isdir(fn):
        if os.path.islink(fn) and os.path.islink(fn) <= follow_links:
            tmp = fn
            fn = os.readlink(fn)
            if verbose:
                print "converting %s (%s)" % (tmp, fn)
        elif verbose:
            print "converting %s" % fn
        f = FileMorpher(fn)
        temp = f.load()
        if mode == 1:
            temp = string.replace(temp, '\n\r', '\n')
            temp = string.replace(temp, '\r', '\n')
        elif mode == 0:
            temp = string.replace(temp, '\n\r', '\r')
            temp = string.replace(temp, '\n', '\r')
        elif mode == 2:
            #this code could be dangerous, but I don't do these
            #conversions often enough to care :-P
            temp = string.replace(temp, '\r', '\n')
            temp = string.replace(temp, '\n', '\n\r')
        stream = f.opentemp()
        stream.write(temp)
        f.commit()

help = """\
cheol:  Converts EOL characters

%s [options] <path ...>
 options:
   -r : recursive
   -l : follow links
   -v : verbose
   -m, --mac : macify line endings
   -u, --unix : unixify line endings
   -d, --dos : dosify line endings
   -h, --help : print help
   --version : print version string
 path is a file or directory"""

if __name__ == '__main__':
    import sys, getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hlvmudr", ("help", "mac", "unix", "dos", "version"))
    except:
        print "That's not an option.  Type -h for help."
        sys.exit(1)
    mode = 1 #default is unix, 0 is mac, 2 is dos
    is_recv = 0 #default isn't recursive
    follow_links = 0 #default don't follow links
    verbose = 0
    for opt in opts:
        if opt[0] == "-r":
            is_recv = 1
        elif opt[0] == "-l":
            follow_links = 1
        elif opt[0] == "-v":
            verbose = 1
        elif opt[0] == "-m" or opt[0] == "--mac":
            mode = 0;
        elif opt[0] == "-u" or opt[0] == "--unix":
            mode = 1;
        elif opt[0] == "-d" or opt[0] == "--dos":
            mode = 2;
        elif opt[0] == "-h" or opt[0] == "--help":
            print help % sys.argv[0]
            sys.exit(0)
        elif opt[0] == "--version":
            print __version__
            sys.exit(0)
    if not args:
        print __version__
    for arg in args:
        convert(arg, mode, is_recv, follow_links, verbose)
