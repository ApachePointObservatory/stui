#!/usr/bin/env python

def epb2d (epb):
    """
    Converts Besselian Epoch to Modified Julian Date
    
    Inputs:
    - epb   Besselian Epoch
    
    Returns the Modified Julian Date (JD - 2400000.5).
    
    Reference:
    Lieske,J.H., 1979. Astron.Astrophys.,73,282.
    
    History:
    P.T.Wallace Starlink    February 1984
    2002-07-11 ROwen  Converted EPB2D to Python.
    """
    return 15019.81352 + (epb-1900.0)*365.242198781


if __name__ == "__main__":
    import RO.MathUtil
    print "testing epb2d"
    # testData is a list of duples consisting of:
    # - input data
    # - the expected output
    testData = (
        (1850, -3242.296419050),
        (1900, 15019.81352000),
        (1950, 33281.92345905),
        (2000, 51544.03339810),
    )
    for testInput, expectedOutput in testData:
        actualOutput = epb2d(testInput)
        if 0 != RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
