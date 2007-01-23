#!/usr/local/bin/python
import Numeric

# Constants
# _RMat is the rotation matrix to convert galactic to ICRS conversion matrix
# (the data is for cpnversion in the other direction,
#  but transposing a rotation matrix inverts it)
_RMat = Numeric.transpose(Numeric.array ((
    (-0.054875539726,   -0.873437108010,   -0.483834985808),
    (+0.494109453312,   -0.444829589425,   +0.746982251810),
    (-0.867666135858,   -0.198076386122,   +0.455983795705),
)))

def icrsFromGal (galP, galV, galEpoch):
    """
    Converts IAU 1958 galactic coordinates to ICRS coordinates.
    Uses the approximation that ICRS = FK5 J2000.
    
    Inputs:
    - galEpoch  epoch of measurement (Julian years);
                used only to correct velocity
    - galP(3)   mean galactic cartesian position (au)
    - galV(3)   galactic cartesian velocity (au/year)
    
    Returns a tuple containing:
    - icrsP(3)  mean ICRS cartesian position (au), a Numeric.array
    - icrsV(3)  mean ICRS cartesian velocity (au/year), a Numeric.array
    
    Error Conditions:
    none
    
    References:
    P.T. Wallace's GalEq routine
    Blaauw et al, Mon.Not.R.Astron.Soc.,121,123 (1960)

    History:
    2002-07-22 ROwen  Converted to Python from the TCC's cnv_Gal2J 4-1.
    """
    galP = Numeric.array(galP)
    galV = Numeric.array(galV)
    
    # correct for velocity (proper motion and radial velocity)
    velAdjP = galP + galV * (2000.0 - galEpoch)

    # convert position to J2000 coordinates
    j2000P = Numeric.matrixmultiply(_RMat, velAdjP)
    j2000V = Numeric.matrixmultiply(_RMat, galV)
    
    return (j2000P, j2000V)


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing icrsFromGal"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((100000, 20000, 30000), (40, 50, 60), 1950.0), (
            (-23112.8248358460, -105635.771521109, -17496.6026284260), 
            (-29.5495170749200, -69.0635469589700, 45.3547409004800), 
        )), 
        (((0, 0, 30000), (40, 50, 60), 1950.0), (
            (-27507.4599294860, -9395.46893160850, 15947.2509161740), 
            (-29.5495170749200, -69.0635469589700, 45.3547409004800), 
        )), 
        (((100000, 0, 30000), (40, 50, 60), 1950.0), (
            (-32995.0139020860, -96739.1797326085, -32436.2476646260), 
            (-29.5495170749200, -69.0635469589700, 45.3547409004800), 
        )), 
        (((100000, 0, 0), (40, 50, 60), 1950.0), (
            (-6965.02982634600, -90796.8881489485, -46115.7615357760), 
            (-29.5495170749200, -69.0635469589700, 45.3547409004800), 
        )), 
        (((100000, 200000, 300000), (40, 50, 60), 2000.0), (
            (-166965.504067600, -235732.544522600, 237808.090492700), 
            (-29.5495170749200, -69.0635469589700, 45.3547409004800), 
        )), 
        (((100000, -200000, 300000), (40, 50, 60), 2050.0), (
            (-363131.809538654, -54347.5314046515, -63252.5472763240), 
            (-29.5495170749200, -69.0635469589700, 45.3547409004800), 
        )), 
        (((-100000, -200000, 300000), (-40, 50, -60), 2050.0), (
            (-357582.200567506, 115657.683448577, 34315.0127162740), 
            (78.9604624061200, 24.5805880164700, 29.3434842805200), 
        )), 
    )
    for testInput, expectedOutput in testData:
        actualOutput = icrsFromGal(*testInput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
