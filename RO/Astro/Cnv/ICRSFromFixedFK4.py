#!/usr/local/bin/python
import Numeric
import RO.PhysConst
import RO.MathUtil
from RO.Astro import llv
from RO.Astro import Tm

# Constants
_MatPP = Numeric.array((
    (+0.999925678186902E+00, -0.111820596422470E-01, -0.485794655896000E-02),
    (+0.111820595717660E-01, +0.999937478448132E+00, -0.271764411850000E-04),
    (+0.485794672118600E-02, -0.271474264980000E-04, +0.999988199738770E+00),
))
_MatVP = Numeric.array((
    (-0.262600477903207E-10, -0.115370204968080E-07, +0.211489087156010E-07),
    (+0.115345713338304E-07, -0.128997445928004E-09, -0.413922822287973E-09),
    (-0.211432713109975E-07, +0.594337564639027E-09, +0.102737391643701E-09),
))

def icrsFromFixedFK4 (fk4P, fk4Date):
    """
    Converts mean catalog fk4 coordinates to ICRS for a fixed star.
    Uses the approximation that ICRS = FK5 J2000.
    
    Inputs:
    - fk4Date   TDB date of fk4 coordinates (Besselian epoch)
                note: TDT will always do and UTC is usually adequate
    - fk4P(3)   mean catalog fk4 cartesian position (au)
    
    Returns:
    - icrsP(3)  ICRS cartesian position (au), a Numeric.array
    
    Error Conditions:
    none
    
    Warnings:
    The FK4 date is in Besselian years.
    
    The star is assumed fixed on the celestial sphere. That is a bit
    different than assuming it has zero proper motion because
    FK4 system has slight ficticious proper motion.
    
    The FK4 system refers to a specific set of precession constants;
    not all Besselian-epoch data was precessed using these constants
    (especially data for epochs before B1950).
    
    References:
    P.T. Wallace's routine FK45Z
    
    History:
    2002-07-09 ROwen  Converted to Python from the TCC's cnv_ZPMFK42J 4-1.
    2004-05-18 ROwen    Stopped importing math; it wasn't used.
    """
    #  compute new precession constants
    #  note: ETrms and PreBn both want Besselian date
    eTerms = llv.etrms (fk4Date)
    precMat = llv.prebn (fk4Date, 1950.0)

    #  subtract e-terms from position. As a minor approximation,
    #  we don't bother to subtract variation in e-terms from proper motion.
    magP = RO.MathUtil.vecMag(fk4P)
    meanFK4P = fk4P - (eTerms * magP)

    #  precess position to B1950, assuming zero fk4 pm
    #  (we'll correct for the fictious fk4 pm later)
    b1950P = Numeric.matrixmultiply(precMat, meanFK4P)

    #  convert position to ICRS (actually FK5 J2000)
    #  but still containing fk4 fictitious pm;
    #  compute fictitious pm.
    tempP = Numeric.matrixmultiply(_MatPP, b1950P)
    ficV  = Numeric.matrixmultiply(_MatVP, b1950P)

    #  correct ICRS position for fk4 fictitious pm
    #  (subtract over period fk4Date to J2000)
    period = 2000.0 - Tm.epJFromMJD (llv.epb2d (fk4Date))
    return tempP - ficV * period


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing icrsFromFixedFK4"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((10000, 20000, 30000), 1850), (8885.75394322159, 20316.6032737176, 30137.6992233812)),
        (((10000, 20000, 30000), 2050), (10368.5105443698, 19886.2202334761, 29950.5314698027)),
        (((10000,     0, 30000), 1850), (9556.06075277268, 327.838213690201, 30142.5859579073)),
        (((10000,     0, 30000), 2050), (10145.0405761217, -112.533352450277, 29951.0735181027)),
        (((    0, 20000, 30000), 1850), (-1107.56704939247, 19981.4447035433, 29991.9292058042)),
        (((    0,     0, 30000), 1850), (-437.260665735273, -7.32044277781096, 29996.8159028686)),
    )
    for testInput, expectedOutput in testData:
        actualOutput = icrsFromFixedFK4(*testInput)
        if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1.0e-14):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
