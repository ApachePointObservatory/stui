#!/usr/bin/env python
"""  
History:    
P.T.Wallace Starlink    21 July 1994
2002-07-11 ROwen    Converted to Python.
2007-04-24 ROwen    Removed unused import of Numeric
"""
from math import sqrt
from vn import vn
from evp import evp
from prenut import prenut
from epj import epj

# Constants
# Light time for 1 au (sec)
_CR = 499.004782
# Gravitational radius of the sun x 2 (2*mu/c**2, au)
_GR2 = 2.0*9.87063e-9

def mappa (eq, tdb):
    """
    Compute star-independent parameters in preparation for
    conversions between mean place and geocentric apparent place.
    
    The parameters produced by this routine are required in the
    parallax, light deflection, aberration, and precession/nutation
    parts of the mean/apparent transformations.
    
    The reference frames and timescales used are post IAU 1976.
    
    Inputs:
    - eq    epoch of mean equinox to be used (Julian)
    - tdb   TDB as a modified Julian date (JD-2400000.5)
    
    Returned a tuple containing the following
    star-independent mean-to-apparent parameters:
    - time interval for proper motion (Julian years)
    - barycentric position of the Earth (au)
    - heliocentric direction of the Earth (unit vector)
    - (grav rad Sun)*2/(Sun-Earth distance)
    - bvc: barycentric velocity of Earth in units of c
    - sqrt(1-v**2) where v=modulus(bvc)
    - precession/nutation (3,3) matrix
    
    References:
    1984 Astronomical Almanac, pp b39-b41.
    (also Lederle & Schwan, Astron. Astrophys. 134,
    1-6, 1984)
    
    Notes:
    
    1)  For tdb, the distinction between the required TDB and TT
    is always negligible.  Moreover, for all but the most
    critical applications UTC is adequate.
    
    2)  The accuracy of the routines using the parameters amprms is
    limited by the routine EVP, used here to compute the
    Earth position and velocity by the methods of Stumpff.
    The maximum error in the resulting aberration corrections is
    about 0.3 milliarcsecond.
    
    3)  The barycentric position of the Earth and
    heliocentric direction of the Earth are referred to
    the mean equinox and equator of epoch eq.
    """
    # Get Earth barycentric and heliocentric position and velocity
    bVel, bPos, hVel, hPos = evp(tdb, eq)

    # Heliocentric direction of earth (normalised) and modulus
    hDir, hDist = vn(hPos)

    # Aberration parameters
    vbc = bVel * _CR
    vbcDir, vbcMag = vn(vbc)

    return (
        # Time interval for proper motion correction (years)
        epj(tdb)-eq,
    
        # Barycentric position of Earth (au)
        bPos,
    
        # Heliocentric direction of earth
        hDir,

        # Light deflection parameter
        _GR2/hDist,
        
        # Barycentric velocity of Earth, in units of C
        vbc,
        
        # sqrt(1-v**2) where v=modulus(bvc)
        sqrt(1.0 - (vbcMag * vbcMag)),
    
        # Precession/nutation matrix
        prenut(eq,tdb),
    )


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing mappa"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        ((1950, 0), (
              -91.1211498973305     ,
            (  0.555854426013983     ,  0.741830433070110     ,  0.321989827457819     ),
            (  0.564027453508102     ,  0.757506968045265     ,  0.328719067064926     ),
              1.997660021202574E-008,
            ( -8.362706113841309E-005,  5.105963334163009E-005,  2.214991041920924E-005),
              0.999999994954405     ,
            (
                    (  0.999754039821038     ,  2.033727159117084E-002,  8.846199508344497E-003),
                    ( -2.033692054832955E-002,  0.999793175039191     , -1.296443809557759E-004),
                    ( -8.847006506463638E-003, -5.029196295524099E-005,  0.999960863207452     ),
            ),
        )),((1950, 30000), (
              -8.98562628336754     ,
            ( -0.265612225902353     ,  0.863968828300309     ,  0.374891214581348     ),
            ( -0.265971401815193     ,  0.884383717910788     ,  0.383568315832724     ),
              2.007656380726188E-008,
            ( -9.736053548152452E-005, -2.462802659885953E-005, -1.067821002867579E-005),
              0.999999994900181     ,
            (
                    (  0.999997626649723     ,  1.998003323760294E-003,  8.687218423237310E-004),
                    ( -1.998044136798959E-003,  0.999998002844512     ,  4.611522516277290E-005),
                    ( -8.686279689779851E-004, -4.785086029884630E-005,  0.999999621597802     ),
            ),
        )),((1950, 60000), (
               73.1498973305954     ,
            ( -0.906641406982486     ,  0.382096779870744     ,  0.165895483671997     ),
            ( -0.906989619242441     ,  0.386401939897297     ,  0.167521256651377     ),
              1.994641703506661E-008,
            ( -4.343606109459875E-005, -8.309340130274852E-005, -3.602307375773933E-005),
              0.999999994955567     ,
            (
                    (  0.999841776244306     , -1.631412968594498E-002, -7.090250293230755E-003),
                    (  1.631386369780481E-002,  0.999866915523857     , -9.535227860407390E-005),
                    (  7.090862280423755E-003, -2.033218525869529E-005,  0.999974859313334     ),
            ),
        )),((2050, 0), (
              -191.121149897330     ,
            (  0.535973731849698     ,  0.754038610440731     ,  0.327294845768089     ),
            (  0.543728427868075     ,  0.769893239771607     ,  0.334101475725700     ),
              1.997660021202574E-008,
            ( -8.495908684768753E-005,  4.917460129981748E-005,  2.133078039406103E-005),
              0.999999994954405     ,
            (
                    (  0.998916209746081     ,  4.268523227561923E-002,  1.855739346188608E-002),
                    ( -4.268449802533320E-002,  0.999088506427428     , -4.358359051314421E-004),
                    ( -1.855908227386648E-002, -3.567494741540564E-004,  0.999827701754139     ),
            ),
        )),((2050, 25000), (
              -122.674880219028     ,
            ( -0.770345528034648     , -0.596206949600702     , -0.258616830949264     ),
            ( -0.761721923240365     , -0.594392451898336     , -0.257831970052751     ),
              1.959704075586911E-008,
            (  6.276047595539008E-005, -6.986930688278237E-005, -3.030482885678343E-005),
              0.999999995130510     ,
            (
                    (  0.999550087168259     ,  2.750824675326232E-002,  1.195489868162080E-002),
                    ( -2.750823538070932E-002,  0.999621563204463     , -1.654173682144005E-004),
                    ( -1.195492484985487E-002, -1.635152220687337E-004,  0.999928523962891     ),
            ),
        )),((2050, 50000), (
              -54.2286105407256     ,
            (  0.952130337849721     ,  0.274365027029354     ,  0.119042265807144     ),
            (  0.956426717736487     ,  0.267875501814115     ,  0.116149253668055     ),
              1.976660661948897E-008,
            ( -3.065227134029836E-005,  8.679211126889806E-005,  3.763508161413279E-005),
              0.999999995055584     ,
            (
                    (  0.999913017911820     ,  1.209697092612376E-002,  5.255464288568359E-003),
                    ( -1.209716844718493E-002,  0.999926826563807     ,  5.796066167055250E-006),
                    ( -5.255009613343668E-003, -6.937179878008020E-005,  0.999986189935400     ),
            ),
        )),((2000, 0), (
              -141.121149897330     ,
            (  0.545955745875526     ,  0.747989169132058     ,  0.324666767226443     ),
            (  0.553920222641464     ,  0.763755907144722     ,  0.331435214258192     ),
              1.997660021202574E-008,
            ( -8.429926449753059E-005,  5.012098335740015E-005,  2.174191977887813E-005),
              0.999999994954405     ,
            (
                    (  0.999409434987316     ,  3.151190219334863E-002,  1.370333092688127E-002),
                    ( -3.151135893253181E-002,  0.999503361135364     , -2.556116899878287E-004),
                    ( -1.370458013074238E-002, -1.763498447413323E-004,  0.999906072280878     ),
            ),
        )),((2000, 30000), (
              -58.9856262833675     ,
            ( -0.277072297009520     ,  0.860935409105613     ,  0.373572720058234     ),
            ( -0.277701823961726     ,  0.881344772189633     ,  0.382247419222596     ),
              2.007656380726188E-008,
            ( -9.702610315073539E-005, -2.571458048475444E-005, -1.115048836131300E-005),
              0.999999994900181     ,
            (
                    (  0.999896778834088     ,  1.317671963061374E-002,  5.727629264426398E-003),
                    ( -1.317698874003437E-002,  0.999913179672220     ,  9.248572949414614E-006),
                    ( -5.727010123923518E-003, -8.472052462546143E-005,  0.999983596954207     ),
            ),
        )),((2000, 60000), (
               23.1498973305954     ,
            ( -0.911651553075419     ,  0.371933152287685     ,  0.161477792745817     ),
            ( -0.912055765986125     ,  0.376234106514626     ,  0.163101737656607     ),
              1.994641703506661E-008,
            ( -4.232890654823059E-005, -8.357279765077009E-005, -3.623144697198072E-005),
              0.999999994955567     ,
            (
                    (  0.999984321865140     , -5.135795174281644E-003, -2.231508871426212E-003),
                    (  5.135711475239192E-003,  0.999986811212154     , -4.323644320908532E-005),
                    (  2.231701494045517E-003,  3.177537962416882E-005,  0.999997509246282     ),
            ),
        )),
    )
    for testInput, expectedOutput in testData:
        actualOutput = mappa(*testInput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-8):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput

