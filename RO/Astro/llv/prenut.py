#!/usr/local/bin/python
import Numeric
from prec import prec
from nut import nut
from epj import epj

def prenut (epoch, mjd):
    """
    Form the matrix of precession and nutation (IAU1976/fk5)
    
    Inputs:
    - epoch     Julian Epoch for mean coordinates
    - mjd       Modified Julian Date (jd-2400000.5) for true coordinates
    
    Returns:
    - pnMat     the combined precession/nutation matrix, a 3x3 Numeric.array.
    
    Notes:
    - The epoch and MJD are TDB (loosely ET).
    - The matrix is in the sense V(true) = pnMat * V(mean)
    
    History:
    P.T.Wallace Starlink    April 1987
    2002-07-11 ROwen  Converted to Python.
    """
    precMat = prec(epoch, epj(mjd))

    # Nutation
    nutMat = nut(mjd)

    # Combine the matrices:  pn = N x P
    return Numeric.matrixmultiply(nutMat, precMat)


if __name__ == "__main__":
    print "testing prenut"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument for nut
    # - the expected resulting matrix
    testData = (
        ((1850,     0), Numeric.array((
            (0.999997599205011     , -2.009238000412708E-003, -8.743837096188619E-004),
            (2.009203289702723E-003,  0.999997980725909     , -4.057394087674096E-005),
            (8.744634667023277E-004,  3.881702884119676E-005,  0.999999616903368     ),
        ))),
        ((1850, 50000), Numeric.array((
            (0.999367699662802     , -3.260570516814452E-002, -1.417987521690844E-002),
            (3.260623722958260E-002,  0.999468256506530     , -1.937253848698750E-004),
            (1.417865171330629E-002, -2.687494829646847E-004,  0.999899441748673     ),
        ))),
        ((1950,     0), Numeric.array((
            (0.999754039821038     ,  2.033727159117084E-002,  8.846199508344497E-003),
            (-2.033692054832955E-002,  0.999793175039191     , -1.296443809557759E-004),
            (-8.847006506463638E-003, -5.029196295524099E-005,  0.999960863207452     ),
        ))),
        ((1950, 15000), Numeric.array((
            (0.999926546774152     ,  1.111471149930000E-002,  4.833657477156983E-003),
            (-1.111475742820590E-002,  0.999938229025119     , -1.736145295591751E-005),
            (-4.833551864963193E-003, -3.636475264850375E-005,  0.999988317658748     ),
        ))),
        ((2050,     0), Numeric.array((
            (0.998916209746081     ,  4.268523227561923E-002,  1.855739346188608E-002),
            (-4.268449802533320E-002,  0.999088506427428     , -4.358359051314421E-004),
            (-1.855908227386648E-002, -3.567494741540564E-004,  0.999827701754139     ),
        ))),
        ((2050, 30000), Numeric.array((
            (0.999647292001725     ,  2.435686237240104E-002,  1.058465157617898E-002),
            (-2.435735990201835E-002,  0.999703312141814     , -8.192246115618234E-005),
            (-1.058350661268479E-002, -1.759206014296547E-004,  0.999943977650609     ),
        ))),
    )
    for testInput, expectedOutput in testData:
        actualOutput = prenut(*testInput)
        if not Numeric.allclose(actualOutput, expectedOutput, rtol=1e-15, atol=1e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput

