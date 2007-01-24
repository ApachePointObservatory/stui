#!/usr/bin/env python
"""Utilities to help in use of Tk canvasses.

History:
2002-03-11 ROwen    Modified to center things properly on unix, as well as Mac classic.
2002-08-08 ROwen    Moved to RO class name.
2002-11-06 ROwen    Fixed a typo in the test code (spiral instead of Spiral);
                    fixed darwin handling assuming aqua Tk (which as the standard Mac offset bug)
2002-11-12 ROwen    Moved the mac fix stuff into RO.Wdg.Canvas.
2003-04-29 ROwen    Fix for Python 2.3: stopped using range for floats.
2004-05-18 ROwen    Removed import sys, since it was not being used.
2004-10-22 ROwen    Modified demo to not use RO.Wdg.PatchedCanvas
                    since it is no longer needed.
2005-06-06 ROwen    Improved Spiral:
                    - Keep track of geom ID for more reliable clear during redraw.
                    - Use list comprehension to speed computation of coords.
2005-06-08 ROwen    Changed Spiral to a new style class.
"""
import math
import Tkinter
import RO.MathUtil

def ctrCircle(cnv, xpos, ypos, rad, width = 1, **kargs):
    """Draws a centered circle on the specified canvas.
    
    Inputs:
    cnv: canvas on which to draw
    xpos: x position
    ypos: y position
    rad: outer radius of circle
    width: thickness of line (inward from radius)
    kargs are arguments for create_oval
    """
    cnv.create_oval(
        xpos - rad,
        ypos - rad,
        xpos + rad,
        ypos + rad,
        width = width,
        **kargs)
        

def ctrPlus(cnv, xpos, ypos, rad, holeRad = 0, width=1, **kargs):
    """Draws a centered + on the specified canvas.
    
    Inputs:
    cnv: canvas on which to draw
    xpos: x position
    ypos: y position
    rad: radius of symbol
    holeRad: radius of hole in center of symbol (0 for none)
    width: thickness of line
    kargs are arguments for create_line
    """
    cnv.create_line(
        xpos, ypos + holeRad,
        xpos, ypos + rad,
        width=width, **kargs)
    cnv.create_line(
        xpos, ypos - holeRad,
        xpos, ypos - rad,
        width=width, **kargs)
    cnv.create_line(
        xpos - holeRad, ypos,
        xpos - rad,     ypos,
        width=width, **kargs)
    cnv.create_line(
        xpos + holeRad, ypos,
        xpos + rad,     ypos,
        width=width, **kargs)

def ctrX(cnv, xpos, ypos, rad, holeRad = 0, width=1, **kargs):
    """Draws a centered X on the specified canvas.
    
    Inputs:
    cnv: canvas on which to draw
    xpos: x position
    ypos: y position
    rad: radius of symbol
    holeRad: radius of hole in center of symbol (0 for none)
    width: thickness of line
    kargs are arguments for create_line
    """
    dxy = (rad / math.sqrt(2))
    holedxy = (holeRad / math.sqrt(2))

    cnv.create_line(
        xpos + holedxy, ypos + holedxy,
        xpos + dxy,     ypos + dxy,
        width=width, **kargs)
    cnv.create_line(
        xpos + holedxy, ypos - holedxy,
        xpos + dxy,     ypos - dxy,
        width=width, **kargs)
    cnv.create_line(
        xpos - holedxy, ypos + holedxy,
        xpos - dxy,     ypos + dxy,
        width=width, **kargs)
    cnv.create_line(
        xpos - holedxy, ypos - holedxy,
        xpos - dxy,     ypos - dxy,
        width=width, **kargs)

class Spiral(object):
    def __init__(self,
        cnv,
        xctr, yctr,
        begRad = 0, endRad = 0,
        begAng = None, endAng = None,
        angOff = 0.0,
        angScale = 1.0, # typically +/- 1.0
        color="black",
        **kargs
    ):
        """Draws a spiral on the specified canvas.
        Allows easy redrawing.
        Allows easy computing of position for drawing objects along the spiral.
        
        Inputs:
        cnv:    the canvas on which to draw
        xctr, yctr: x and y positions of center of spiral
        begRad, endRad: starting and ending radius of spiral;
            if begRad and endRad both = 0, no spiral is drawn
        begAng, endAng: angle of starting and ending points of spiral;
            if None then no spiral is drawn
        angOff: the angle displayed when ang = 0
        angScale: a multipler; typically +/-1.0 to set CW or CCW increase in direction
            the displayed angle = (ang * angScale) + angOff;
            a displayed angle of 0 is along +x (right), 90 is along -y (up)
        color:  color of spiral
        kargs:  additional keyword arguments for drawing the spiral,
            specifically for the Tkinter.Canvas.create_line method
        """
        self.cnv = cnv
        self.cnvID = None
        self.setAngOffScale(angOff, angScale, redraw=0)
        self.setGeom(xctr, yctr, begRad, endRad, redraw=0)
        self.setAngLim(begAng, endAng, redraw=0)
        self.dAng = 10.0

        # handle drawing arguments;
        # default is an arrow that looks like a butt
        # (since there are errors in drawing a butt)
        # but this can be overridded by specifying capstyle
        defKArgs = {
            "smooth":1,
            "arrow":"both",
            "arrowshape":(0,0,3),
        }
        if kargs.has_key("capstyle"):
            del(defKArgs["arrow"])
            del(defKArgs["arrowshape"])
        self.drawKArgs = defKArgs
        self.drawKArgs.update(kargs)
        self.drawKArgs["fill"] = color
        
        self.draw()
    
    def getAngLim(self):
        """Returns (beginning angle, ending angle)"""
        return (self.begAng, self.endAng)
    
    def setAngOffScale(self, angOff, angScale, redraw=1):
        self.angOff = angOff
        self.angScale = angScale
        if redraw:
            self.draw()

    def setAngLim(self, begAng, endAng, redraw=True):
        if (begAng != None) and (begAng == endAng):
            raise RuntimeError, "angle range must be nonzero (though it may be None)"
        self.begAng = begAng
        self.endAng = endAng
        if redraw:
            self.draw()
    
    def setGeom(self, xctr, yctr, begRad, endRad, redraw=1):
        self.xctr = xctr
        self.yctr = yctr
        self.begRad = begRad
        self.endRad = endRad
        if redraw:
            self.draw()
    
    def draw(self):
        if self.cnvID != None:
            self.cnv.delete(self.cnvID)

        if (None in (self.begAng, self.endAng)) or (int(max(self.begRad, self.endRad)) <= 0):
            return

        nPts = 1 + int(round((self.endAng - self.begAng) / float(self.dAng)))
        lineCoords = [
            self.angToXY(self.begAng + (ind*self.dAng)) for ind in range(nPts)
        ]
        self.cnvID = self.cnv.create_line(*lineCoords, **self.drawKArgs)
    
    def angToXY(self, ang, doLimit=1):
        """Returns x,y pixel coordinates for an angle along a spiral.
        Angle 0 is +x (right), 90 is -y (up).
        """
        if None in (self.begAng, self.endAng):
            return [None, None]

        if doLimit:
            self.minAng = min(self.begAng, self.endAng)
            self.maxAng = max(self.begAng, self.endAng)
            if ang > self.maxAng:
                ang = self.maxAng
            elif ang < self.minAng:
                ang = self.minAng

        radialPixPerDeg = float(self.endRad - self.begRad) / (self.endAng - self.begAng)
        radPix = self.begRad + (radialPixPerDeg * (ang - self.begAng))

        adjAng = (ang * self.angScale) + self.angOff
        xPos = self.xctr + (radPix * RO.MathUtil.cosd(adjAng))
        yPos = self.yctr - (radPix * RO.MathUtil.sind(adjAng))
        return (xPos, yPos)

if __name__ == '__main__':
    from RO.Wdg.PythonTk import PythonTk
    root = PythonTk()

    cnv = Tkinter.Canvas (root, width=201, height=201)
    cnv.pack()
    ctrPlus  (cnv,  80,  80, 10, 5)
    ctrPlus  (cnv, 100,  80, 10, 5, 5)
    ctrX     (cnv,  80, 100, 10, 5)
    ctrX     (cnv, 100, 100, 10, 5, 5)
    ctrCircle(cnv,  80, 120, 10, 1)
    ctrCircle(cnv, 100, 120, 10, 5)

    ctrCircle(cnv, 120,  80, 10)
    ctrPlus  (cnv, 120,  80, 10, holeRad = 5)
    ctrX     (cnv, 120,  80, 10, holeRad = 5)
    
    ctrCircle(cnv, 120, 100, 10, width = 5)
    ctrPlus  (cnv, 120, 100, 10, holeRad = 5, width = 5)
    ctrX     (cnv, 120, 100, 10, holeRad = 5, width = 5)
    aSpiral = Spiral(
        cnv = cnv,
        xctr = 100, yctr = 100,
        begRad = 75, endRad = 90,
        begAng = -360, endAng = 360,
        angOff = 90.0,
        angScale = -1.0,
    )

    root.mainloop()
