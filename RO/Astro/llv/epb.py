#!/usr/local/bin/python

def epb (mjd):
    """
    Converts Modified Julian Date to Besselian Epoch
    
    Inputs:
    - mjd   Modified Julian Date (JD - 2400000.5)
    
    Returns the Besselian Epoch.
    
    Reference:
    Lieske,J.H., 1979. Astron.Astrophys.,73,282.
    
    History:
    P.T.Wallace Starlink    February 1984
    2002-07-11 ROwen  Converted EPB2D to Python.
    """
    return 1900.0 + (mjd-15019.81352)/365.242198781


if __name__ == "__main__":
    import RO.MathUtil
    print "testing epb"
    # testData is a list of duples consisting of:
    # - input data
    # - the expected output
    testData = (
        (    0, 1858.87711340549),
        (15000, 1899.94575238002),
        (30000, 1941.01439135455),
        (50000, 1995.77257665392),
        (75000, 2064.22030827814),
    )
    for testInput, expectedOutput in testData:
        actualOutput = epb(testInput)
        if 0 != RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
