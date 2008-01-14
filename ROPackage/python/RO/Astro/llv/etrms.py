#!/usr/bin/env python
"""
History:
P.T.Wallace Starlink    10 April 1990
2002-07-11 ROwen    Converted to Python.
2007-04-24 ROwen    Converted from Numeric to numpy.
"""
import math
import numpy
import RO.PhysConst

def etrms (bep):
    """
    Compute the e-terms (elliptic component of annual aberration)
    vector (double precision)
    
    Inputs:
    - bep       Besselian epoch
    
    Returns:
    - etrms     the e-terms (dx, dy, dz) as a numpy.array.
    
    Converted from Pat Wallace's ETRMS. His notes follow:
    
    Note the use of the J2000 aberration constant (20.49552 arcsec).
    This is a reflection of the fact that the e-terms embodied in
    existing star catalogues were computed from a variety of
    aberration constants.  Rather than adopting one of the old
    constants the latest value is used here.
    
    References:
    1  Smith, C.A. et al., 1989.  Astr.j. 97, 265.
    2  Yallop, B.D. et al., 1989.  Astr.j. 97, 274.
    """
    # Julian centuries since B1950
    t=(bep-1950.0)*1.00002135903e-2

    # Eccentricity
    e=0.01673011-(0.00004193+0.000000126*t)*t

    # Mean obliquity
    e0=(84404.836-(46.8495+(0.00319+0.00181*t)*t)*t)*RO.PhysConst.RadPerArcSec

    # Mean longitude of perihelion
    p=(1015489.951+(6190.67+(1.65+0.012*t)*t)*t)*RO.PhysConst.RadPerArcSec

    # e-terms
    ek=e*20.49552*RO.PhysConst.RadPerArcSec
    cp=math.cos(p)
    return numpy.array((
         ek*math.sin(p),
        -ek*cp*math.cos(e0),
        -ek*cp*math.sin(e0),
    ))


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing etrms"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (1850, (-1.639366574920955E-006, -2.749622395006071E-007, -1.193219662408752E-007)),
        (1900, (-1.632651752763173E-006, -2.971343833660797E-007, -1.289036408923716E-007)),
        (1950, (-1.625574151689435E-006, -3.191905500580295E-007, -1.384290374442590E-007)),
        (1975, (-1.621900014009299E-006, -3.301735556749691E-007, -1.431699576964520E-007)),
        (2000, (-1.618136038053575E-006, -3.411256675648316E-007, -1.478960019791259E-007)),
    )
    for testInput, expectedOutput in testData:
        actualOutput = etrms(testInput)
        if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
