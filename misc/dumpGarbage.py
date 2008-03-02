#!/usr/bin/env python
import gc
"""Test garbage collection
From Python Cookbook 2nd ed.
"""
def dumpGarbage():
    print "\nGARBAGE:"
    gc.collect()
    print "\nGARBAGE OBJECTS:"
    for x in gc.garbage:
        s = str(x)
        if len(s) > 80: s = s[:77] + "..."
        print "%s\n  %s" % (type(x), s)
        
if __name__ == "__main__":
    gc.enable()
    gc.set_debug(gc.DEBUG_LEAK)
    # simulate a leak
    l = []
    l.append(l)
    del l
    dumpGarbage()
