"""PVT implements a class to describe (position, velocity, time) triplets.

History:
2001-01-10 ROwen    Modified floatCnv to not handle NaN floating values,
    since this failed on Mac OS X; it will still handle string "NaN" (any case).
2002-08-08 ROwen    Modified to use new Astro.Tm functions which are in days, not sec.
2003-05-08 ROwen    Modified to use RO.CnvUtil.
2003-11-21 ROwen    Bug fix: __init__ did not check the data.
2005-06-08 ROwen    Changed PVT to a new-style class.
"""
import time
import types
import RO.Astro.Tm
import RO.CnvUtil
import RO.MathUtil
import RO.PhysConst

class PVT(object):
    """Defines a position, velocity, time triplet, where time is in TAI.
    
    Inputs:
    - pos   position
    - vel   velocity (in units of position/sec)
    - time  TAI, MJD seconds
    
    Each value must be one of: a float, a string representation of a float,
    "NaN" (any case) or None. "NaN" and None mean "unknown" and are stored as None.

    Raises ValueError if any value is invalid.
    """
    def __init__(self, pos=None, vel=0.0, t=0.0):
        self.pos = None
        self.vel = 0.0
        self.t = 0.0
        self.set(pos, vel, t)

    def __repr__(self):
        return "PVT(%s, %s, %s)" % (str(self.pos), str(self.vel), str(self.t))


    def set(self, pos=None, vel=None, t=None):
        """Sets pos, vel and t; all default to their current values

        Each value must be one of: a float, a string representation of a float,
        "NaN" (any case) or None. "NaN" means "unknown".and is stored as None.

        Errors:
        Raises ValueError if any value is invalid.
        """
        if pos != None:
            self.pos = RO.CnvUtil.asFloatOrNone(pos)
        if vel != None:
            self.vel = RO.CnvUtil.asFloatOrNone(vel)
        if t != None:
            self.t = RO.CnvUtil.asFloatOrNone(t)


    def isValid(self):
        """Returns true if the pvt is valid, false otherwise.

        A pvt is valid if all values are defined (not None or NaN) and time > 0.
        """
        return  (self.pos != None) \
            and (self.vel != None) \
            and (self.t != None) \
            and (self.t > 0)


    def getPos(self, t=None):
        """Returns the position at the specified time.
        Time defaults to the current TAI.

        Returns None if the pvt is invalid.
        """
        if not self.isValid():
            return None

        if t == None:
            t = RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay
    
        return self.pos + (self.vel * (t - self.t))



if __name__ == "__main__":
    print "\nrunning PVT test"
    
    currTAI = RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay

    varList = (
        PVT(),
        PVT(25),
        PVT(25, 0, currTAI),
        PVT(25, 1),
        PVT(25, 1, currTAI),
        PVT('NaN', 'NaN', 'NaN')
    )

    for i in range(5):
        t = RO.Astro.Tm.taiFromPySec() * RO.PhysConst.SecPerDay
        print "\ntime =", t
        for var in varList:
            print var, "pos =", var.getPos(t)
        if i < 4:
            time.sleep(1)
