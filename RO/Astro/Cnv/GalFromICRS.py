#!/usr/local/bin/python
import Numeric

# Constants
# _RMat is the rotation matrix to convert ICRS to galactic coordinates
_RMat = Numeric.array ((
    (-0.054875539726,   -0.873437108010,   -0.483834985808),
    (+0.494109453312,   -0.444829589425,   +0.746982251810),
    (-0.867666135858,   -0.198076386122,   +0.455983795705),
))

def galFromICRS (icrsP, icrsV, galEpoch):
    """
    Converts ICRS coordinates to IAU 1958 galactic coordinates.

    Inputs:
    - icrsP(3)  mean ICRS cartesian position (au)
    - icrsV(3)  mean ICRS cartesian velocity (au/year)
    - galEpoch  epoch of measurement (Julian years);
                used only to correct velocity
    
    Returns:
    - galP(3)   mean galactic cartesian position (au), a Numeric.array
    - galV(3)   galactic cartesian velocity (au/year), a Numeric.array

    Warnings:
    Uses the approximation that ICRS = FK5 J2000.
    
    Error Conditions:
    none
    
    References:
    P.T. Wallace's EqGal routine
    Blaauw et al, Mon.Not.R.Astron.Soc.,121,123 (1960)

    History:
    2002-07-17 ROwen  Converted to Python from the TCC's cnv_J2Gal 4-1.
    """
    icrsP = Numeric.array(icrsP)
    icrsV = Numeric.array(icrsV)
    
    # correct for velocity (proper motion and radial velocity)
    velAdjP = icrsP + icrsV * (galEpoch - 2000.0)
    
    # convert position and velocity to galactic coordinates
    galP = Numeric.matrixmultiply (_RMat, velAdjP)
    galV = Numeric.matrixmultiply (_RMat,  icrsV)
    
    return (galP, galV)


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing galFromICRS"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((200000, 300000, 100000), (20, 40, 60), 1950), (
            (-318136.484215830, 38225.8419860080, -187461.895916713),
            (-65.0650942634000, 36.9079405978400, 2.08264958026000),
        )),
        (((200000, 300000, 100000), (20, 40, 60), 2000), (
            (-321389.738929000, 40071.2390159000, -187357.763437700),
            (-65.0650942634000, 36.9079405978400, 2.08264958026000),
        )),
        (((200000, 300000, 100000), (20, 40, 60), 2050), (
            (-324642.993642170, 41916.6360457920, -187253.630958687),
            (-65.0650942634000, 36.9079405978400, 2.08264958026000),
        )),
        (((200000, -300000, -100000), (-20, 40, 60), 2050), (
            (296296.019404882, 158429.720432168, -157869.226154771),
            (-62.8700726743600, 17.1435624653600, 36.7892950145800),
        )),
        (((200000, 000000, 000000), (-20, 40, 60), 2050), (
            (-14118.6115789180, 99679.0687856680, -171693.762420871),
            (-62.8700726743600, 17.1435624653600, 36.7892950145800),
        )),
        (((000000, 000000, 300000), (-20, 40, 60), 2050), (
            (-148293.999376118, 224951.853666268, 138634.603462229),
            (-62.8700726743600, 17.1435624653600, 36.7892950145800),
        )),
        (((000000, 100000, 000000), (-20, 40, 60), 2050), (
            (-90487.2144347180, -43625.7808192320, -17968.1738614710),
            (-62.8700726743600, 17.1435624653600, 36.7892950145800),
        )),
    )
    for testInput, expectedOutput in testData:
        actualOutput = galFromICRS(*testInput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
