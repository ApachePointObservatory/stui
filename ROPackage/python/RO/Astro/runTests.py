#!/usr/bin/env python
"""
Run Astro test code in Astro package.

Warning: does not report a summary at the end;
you'll have to scan the output to see errors!
Eventually I hope to switch to unittest to solve this.
"""
import os.path
import subprocess

thisFile = os.path.basename(__file__)

isFirst = True
for dirpath, dirnames, filenames in os.walk("."):
    # strip invisible directories and files
    newdirnames = [dn for dn in dirnames if not dn.startswith(".")]
    dirnames[:] = newdirnames
    
    # don't test modules in the root directory
    if isFirst:
        isFirst = False
        continue
    

    # test all modules
    print "Testing modules in", os.path.basename(dirpath)
    for filename in filenames:
        if not filename.endswith(".py"):
            continue
        if filename.startswith("."):
            continue
        subprocess.call(["python", os.path.join(dirpath, filename)])
