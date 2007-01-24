#!/usr/bin/env python
"""Examine which mouse button is which.
"""
import Tkinter

root = Tkinter.Tk()
f = Tkinter.Label(text="Press mouse buttons here")
f.pack(side="left")
# leave room for grow box..
Tkinter.Label(text="  ").pack(side="left")

class DoButton:
    def __init__(self, butNum):
        self.butNum = butNum
    def __call__(self, evt):
        evtNum = getattr(evt, "num", "(absent)")
        f["text"] = "Button = %s; event.num = %s" % (self.butNum, evtNum)

for ii in range(1,4):
    root.bind("<Button-%d>" % ii, DoButton(ii))

root.mainloop()
