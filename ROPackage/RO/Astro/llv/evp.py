#!/usr/bin/env python
__all__ = ["evp"]

from math import sin, cos, pi, sqrt, fmod
import Numeric
from prec import prec
from epj import epj

# Constants
TWOPI = pi * 2.0
DS2R = 0.7272205216643e-4
B1950 = 1949.9997904423

# Constants DCFEL(I,k) of fast changing elements
# I=1                    I=2                  I=3
DCFEL = Numeric.array((
    (1.7400353e+00, 6.2833195099091e+02, 5.2796e-06),
    (6.2565836e+00, 6.2830194572674e+02,-2.6180e-06),
    (4.7199666e+00, 8.3997091449254e+03,-1.9780e-05),
    (1.9636505e-01, 8.4334662911720e+03,-5.6044e-05),
    (4.1547339e+00, 5.2993466764997e+01, 5.8845e-06),
    (4.6524223e+00, 2.1354275911213e+01, 5.6797e-06),
    (4.2620486e+00, 7.5025342197656e+00, 5.5317e-06),
    (1.4740694e+00, 3.8377331909193e+00, 5.6093e-06),
))

# Constants DCEPS and CCSEL(I,k) of slowly changing elements
# I=1             I=2             I=3
DCEPS = Numeric.array ((4.093198e-01,-2.271110e-04,-2.860401e-08))
CCSEL = Numeric.array ((
    (1.675104E-02,-4.179579E-05,-1.260516E-07),
    (2.220221E-01, 2.809917E-02, 1.852532E-05),
    (1.589963E+00, 3.418075E-02, 1.430200E-05),
    (2.994089E+00, 2.590824E-02, 4.155840E-06),
    (8.155457E-01, 2.486352E-02, 6.836840E-06),
    (1.735614E+00, 1.763719E-02, 6.370440E-06),
    (1.968564E+00, 1.524020E-02,-2.517152E-06),
    (1.282417E+00, 8.703393E-03, 2.289292E-05),
    (2.280820E+00, 1.918010E-02, 4.484520E-06),
    (4.833473E-02, 1.641773E-04,-4.654200E-07),
    (5.589232E-02,-3.455092E-04,-7.388560E-07),
    (4.634443E-02,-2.658234E-05, 7.757000E-08),
    (8.997041E-03, 6.329728E-06,-1.939256E-09),
    (2.284178E-02,-9.941590E-05, 6.787400E-08),
    (4.350267E-02,-6.839749E-05,-2.714956E-07),
    (1.348204E-02, 1.091504E-05, 6.903760E-07),
    (3.106570E-02,-1.665665E-04,-1.590188E-07),
))

# Constants of the arguments of the short-period perturbations
# by the planets:   DCARGS(I,k)
# I=1                   I=2
DCARGS = Numeric.array ((
    (5.0974222e+00,-7.8604195454652e+02),
    (3.9584962e+00,-5.7533848094674e+02),
    (1.6338070e+00,-1.1506769618935e+03),
    (2.5487111e+00,-3.9302097727326e+02),
    (4.9255514e+00,-5.8849265665348e+02),
    (1.3363463e+00,-5.5076098609303e+02),
    (1.6072053e+00,-5.2237501616674e+02),
    (1.3629480e+00,-1.1790629318198e+03),
    (5.5657014e+00,-1.0977134971135e+03),
    (5.0708205e+00,-1.5774000881978e+02),
    (3.9318944e+00, 5.2963464780000e+01),
    (4.8989497e+00, 3.9809289073258e+01),
    (1.3097446e+00, 7.7540959633708e+01),
    (3.5147141e+00, 7.9618578146517e+01),
    (3.5413158e+00,-5.4868336758022e+02),
))

# Amplitudes CCAMPS(N,k) of the short-period perturbations
# N=1            N=2             N=3             N=4             N=5
CCAMPS = Numeric.array ((
    (-2.279594E-5, 1.407414E-5, 8.273188E-6, 1.340565E-5,-2.490817E-7),
    (-3.494537E-5, 2.860401E-7, 1.289448E-7, 1.627237E-5,-1.823138E-7),
    (6.593466E-7, 1.322572E-5, 9.258695E-6,-4.674248E-7,-3.646275E-7),
    (1.140767E-5,-2.049792E-5,-4.747930E-6,-2.638763E-6,-1.245408E-7),
    (9.516893E-6,-2.748894E-6,-1.319381E-6,-4.549908E-6,-1.864821E-7),
    (7.310990E-6,-1.924710E-6,-8.772849E-7,-3.334143E-6,-1.745256E-7),
    (-2.603449E-6, 7.359472E-6, 3.168357E-6, 1.119056E-6,-1.655307E-7),
    (-3.228859E-6, 1.308997E-7, 1.013137E-7, 2.403899E-6,-3.736225E-7),
    (3.442177E-7, 2.671323E-6, 1.832858E-6,-2.394688E-7,-3.478444E-7),
    (8.702406E-6,-8.421214E-6,-1.372341E-6,-1.455234E-6,-4.998479E-8),
    (-1.488378E-6,-1.251789E-5, 5.226868E-7,-2.049301E-7, 0.0E0),
    (-8.043059E-6,-2.991300E-6, 1.473654E-7,-3.154542E-7, 0.0E0),
    (3.699128E-6,-3.316126E-6, 2.901257E-7, 3.407826E-7, 0.0E0),
    (2.550120E-6,-1.241123E-6, 9.901116E-8, 2.210482E-7, 0.0E0),
    (-6.351059E-7, 2.341650E-6, 1.061492E-6, 2.878231E-7, 0.0E0),
))

# Constants of the secular perturbations in longitude
# CCSEC3 and CCSEC(N,k)
# N=1             N=2             N=3
CCSEC3 = -7.757020E-08
CCSEC = Numeric.array ((
    (1.289600E-06, 5.550147E-01, 2.076942E+00),
    (3.102810E-05, 4.035027E+00, 3.525565E-01),
    (9.124190E-06, 9.990265E-01, 2.622706E+00),
    (9.793240E-07, 5.508259E+00, 1.559103E+01),
))

# Sidereal rate DCSLD in longitude, rate CCSGD in mean anomaly
DCSLD = 1.990987e-07
CCSGD = 1.990969E-07

# Some constants used in the calculation of the lunar contribution
CCKM = 3.122140E-05
CCMLD = 2.661699E-06
CCFDI = 2.399485E-07

# Constants DCARGM(I,k) of the arguments of the perturbations
# of the motion of the Moon
# I=1                   I=2
DCARGM = Numeric.array ((
    (5.1679830e+00, 8.3286911095275e+03),
    (5.4913150e+00,-7.2140632838100e+03),
    (5.9598530e+00, 1.5542754389685e+04),
))

# Amplitudes CCAMPM(N,k) of the perturbations of the Moon
# N=1            N=2              N=3             N=4
CCAMPM = Numeric.array ((
    (1.097594E-01, 2.896773E-07, 5.450474E-02, 1.438491E-07),
    (-2.223581E-02, 5.083103E-08, 1.002548E-02,-2.291823E-08),
    (1.148966E-02, 5.658888E-08, 8.249439E-03, 4.063015E-08),
))

# CCPAMV[k]=A*M*dl/t (planets), DC1MME=1-mass(Earth+Moon)
CCPAMV = Numeric.array ((8.326827E-11,1.843484E-11,1.988712E-12,1.881276E-12))
DC1MME = 0.99999696

# CCPAM[k]=A*M(planets), CCIM=inclination(Moon)
CCPAM = Numeric.array ((4.960906E-3,2.727436E-3,8.392311E-4,1.556861E-3))
CCIM = 8.978749E-2


def evp (tdb, deqx = 0.0):
    """
    Barycentric and heliocentric velocity and position of the Earth
    
    Inputs:
    - tdb   TDB date (loosely et) as a Modified Julian Date
    - deqx  Julian Epoch (e.g. 2000.0) of mean equator and
            equinox of the vectors returned. If deqx <= 0.0,
            all vectors are referred to the mean equator and
            equinox (fk5) of epoch date.
    
    Returns a tuple consisting of (all Numeric.array(3)):
    - Barycentric velocity of Earth (au/s)
    - Barycentric position of Earth (au)
    - Heliocentric velocity of Earth (au/s)
    - Heliocentric position of Earth (au)
    
    Accuracy:
    
    The maximum deviations from the JPL DE96 ephemeris are as
    follows:
    
    barycentric velocity    0.42  m/s
    barycentric position    6900  km
    
    heliocentric velocity   0.42  m/s
    heliocentric position   1600  km
    
    This routine is adapted from the barvel and barcor
    subroutines of P.Stumpff, which are described in
    Astron. Astrophys. Suppl. Ser. 41, 1-8 (1980).  Most of the
    changes are merely cosmetic and do not affect the results at
    all.  However, some adjustments have been made so as to give
    results that refer to the new (IAU 1976 'fk5') equinox
    and precession, although the differences these changes make
    relative to the results from Stumpff's original 'fk4' version
    are smaller than the inherent accuracy of the algorithm.  One
    minor shortcoming in the original routines that has not been
    corrected is that better numerical accuracy could be achieved
    if the various polynomial evaluations were nested.  Note also
    that one of Stumpff's precession constants differs by 0.001 arcsec
    from the value given in the Explanatory Supplement to the A.E.
    
    History:
    P.t.Wallace Starlink    21 November 1994
    2002-07-11 ROwen  Converted to Python.
    """
    
    # note: in the original code, E was a shortcut for sorbel[0]
    # and G was a shortcut for forbel[0]

    # time arguments
    t = (tdb-15019.5)/36525.0
    tsq = t*t

    # Values of all elements for the instant date
    forbel = [0.0]*7
    for k in range(8):
        dlocal = fmod(DCFEL[k,0]+t*DCFEL[k,1]+tsq*DCFEL[k,2], TWOPI)
        if k == 0:
            dml = dlocal
        else:
            forbel[k-1] = dlocal
    deps = fmod(DCEPS[0]+t*DCEPS[1]+tsq*DCEPS[2], TWOPI)
    sorbel = [fmod(CCSEL[k,0]+t*CCSEL[k,1]+tsq*CCSEL[k,2], TWOPI)
                for k in range(17)]

    # Secular perturbations in longitude
    sn = [sin(fmod(CCSEC[k,1]+t*CCSEC[k,2], TWOPI))
            for k in range(4)]

    # Periodic perturbations of the emb (Earth-Moon barycentre)
    pertl =  CCSEC[0,0]      *sn[0] +CCSEC[1,0]*sn[1]+  \
        (CCSEC[2,0]+t*CCSEC3)*sn[2] +CCSEC[3,0]*sn[3]
    pertld = 0.0
    pertr = 0.0
    pertrd = 0.0
    for k in range(15):
        A = fmod(DCARGS[k,0]+t*DCARGS[k,1], TWOPI)
        cosa = cos(A)
        sina = sin(A)
        pertl = pertl + CCAMPS[k,0]*cosa+CCAMPS[k,1]*sina
        pertr = pertr + CCAMPS[k,2]*cosa+CCAMPS[k,3]*sina
        if k < 11:
            pertld = pertld+  \
                (CCAMPS[k,1]*cosa-CCAMPS[k,0]*sina)*CCAMPS[k,4]
            pertrd = pertrd+  \
                (CCAMPS[k,3]*cosa-CCAMPS[k,2]*sina)*CCAMPS[k,4]

    # Elliptic part of the motion of the emb
    esq = sorbel[0]*sorbel[0]
    dparam = 1.0-esq
    param = dparam
    twoe = sorbel[0]+sorbel[0]
    twog = forbel[0]+forbel[0]
    phi = twoe*((1.0-esq*0.125)*sin(forbel[0])+sorbel[0]*0.625*sin(twog)  \
        +esq*0.5416667*sin(forbel[0]+twog) )
    F = forbel[0]+phi
    sinf = sin(F)
    cosf = cos(F)
    dpsi = dparam/(1.0+(sorbel[0]*cosf))
    phid = twoe*CCSGD*((1.0+esq*1.5)*cosf+sorbel[0]*(1.25-sinf*sinf*0.5))
    psid = CCSGD*sorbel[0]*sinf/sqrt(param)

    # Perturbed heliocentric motion of the emb
    d1pdro = 1.0+pertr
    drd = d1pdro*(psid+dpsi*pertrd)
    drld = d1pdro*dpsi*(DCSLD+phid+pertld)
    dtl = fmod(dml+phi+pertl, TWOPI)
    dsinls = sin(dtl)
    dcosls = cos(dtl)
    dxhd = drd*dcosls-drld*dsinls
    dyhd = drd*dsinls+drld*dcosls

    # Influence of eccentricity, evection and variation on the
    # geocentric motion of the Moon
    pertl = 0.0
    pertld = 0.0
    pertp = 0.0
    pertpd = 0.0
    for k in range(3):
        A = fmod(DCARGM[k,0]+t*DCARGM[k,1], TWOPI)
        sina = sin(A)
        cosa = cos(A)
        pertl = pertl +CCAMPM[k,0]*sina
        pertld = pertld+CCAMPM[k,1]*cosa
        pertp = pertp +CCAMPM[k,2]*cosa
        pertpd = pertpd-CCAMPM[k,3]*sina

    # Heliocentric motion of the Earth
    tl = forbel[1]+pertl
    sinlm = sin(tl)
    coslm = cos(tl)
    sigma = CCKM/(1.0+pertp)
    A = sigma*(CCMLD+pertld)
    B = sigma*pertpd
    dxhd = dxhd+(A*sinlm)+(B*coslm)
    dyhd = dyhd-(A*coslm)+(B*sinlm)
    dzhd =    -(sigma*CCFDI*cos(forbel[2]))

    # Barycentric motion of the Earth
    dxbd = dxhd*DC1MME
    dybd = dyhd*DC1MME
    dzbd = dzhd*DC1MME
    sinlp = [0.0] * 4
    coslp = [0.0] * 4
    for k in range(4):
        plon = forbel[k+3]
        pomg = sorbel[k+1]
        pecc = sorbel[k+9]
        tl = fmod(plon+2.0*pecc*sin(plon-pomg), TWOPI)
        sinlp[k] = sin(tl)
        coslp[k] = cos(tl)
        dxbd = dxbd+(CCPAMV[k]*(sinlp[k]+pecc*sin(pomg)))
        dybd = dybd-(CCPAMV[k]*(coslp[k]+pecc*cos(pomg)))
        dzbd = dzbd-(CCPAMV[k]*sorbel[k+13]*cos(plon-sorbel[k+5]))

    # Transition to mean equator of date
    dcosep = cos(deps)
    dsinep = sin(deps)
    dyahd = dcosep*dyhd-dsinep*dzhd
    dzahd = dsinep*dyhd+dcosep*dzhd
    dyabd = dcosep*dybd-dsinep*dzbd
    dzabd = dsinep*dybd+dcosep*dzbd

    # Heliocentric coordinates of the Earth
    dr = dpsi*d1pdro
    flatm = CCIM*sin(forbel[2])
    A = sigma*cos(flatm)
    dxh = dr*dcosls-(A*coslm)
    dyh = dr*dsinls-(A*sinlm)
    dzh =   -(sigma*sin(flatm))

    # Barycentric coordinates of the Earth
    dxb = dxh*DC1MME
    dyb = dyh*DC1MME
    dzb = dzh*DC1MME
    for k in range(4):
        flat = sorbel[k+13]*sin(forbel[k+3]-sorbel[k+5])
        A = CCPAM[k]*(1.0-sorbel[k+9]*cos(forbel[k+3]-sorbel[k+1]))
        B = A*cos(flat)
        dxb = dxb-(B*coslp[k])
        dyb = dyb-(B*sinlp[k])
        dzb = dzb-(A*sin(flat))

    # Transition to mean equator of date
    dyah = dcosep*dyh-dsinep*dzh
    dzah = dsinep*dyh+dcosep*dzh
    dyab = dcosep*dyb-dsinep*dzb
    dzab = dsinep*dyb+dcosep*dzb

    # Copy result components into vectors, correcting for fk4 equinox
    depj=epj(tdb)
    deqcor = DS2R*(0.035+0.00085*(depj-B1950))
    helVel = Numeric.array((
        dxhd-deqcor*dyahd,
        dyahd+deqcor*dxhd,
        dzahd,
    ))
    barVel = Numeric.array((
        dxbd-deqcor*dyabd,
        dyabd+deqcor*dxbd,
        dzabd,
    ))
    helPos = Numeric.array((
        dxh-deqcor*dyah,
        dyah+deqcor*dxh,
        dzah,
    ))
    barPos = Numeric.array((
        dxb-deqcor*dyab,
        dyab+deqcor*dxb,
        dzab,
    ))

    # Was precession to another equinox requested?
    if deqx > 0.0:

        # Yes: compute precession matrix from mjd date to Julian epoch deqx
        dprema = prec(depj,deqx)
    
        # Rotate helVel
        helVel = Numeric.matrixmultiply(dprema, helVel)
    
        # Rotate barVel
        barVel = Numeric.matrixmultiply(dprema, barVel)
    
        # Rotate helPos
        helPos = Numeric.matrixmultiply(dprema, helPos)
    
        # Rotate barPos
        barPos = Numeric.matrixmultiply(dprema, barPos)
    
    return (barVel, barPos, helVel, helPos)


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing evp"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        ((    0,    0), (
            (-1.650696327163707E-007,  1.057102681082382E-007,  4.586157127466983E-008),
            (0.573675055123641     ,  0.730328832856318     ,  0.316986924591936     ),
            (-1.651684055052331E-007,  1.057264124985974E-007,  4.587122542133332E-008),
            (0.575365816589401     ,  0.737048555374318     ,  0.319829334517141     ),
        )),
        ((15000,    0), (
            (-1.993022307429824E-007,  3.177637675047169E-008,  1.379070071699878E-008),
            (0.178029409163994     ,  0.894423994342947     ,  0.387905841453252     ),
            (-1.992202454159510E-007,  3.173288271614674E-008,  1.376955153842574E-008),
            (0.174575062713974     ,  0.888711527912832     ,  0.385540714439554     ),
        )),
        ((15000, 1850), (
            (-1.988658728318745E-007,  3.399827483135094E-008,  1.475746103133701E-008),
            (0.189881781401266     ,  0.892370939892429     ,  0.387012543394413     ),
            (-1.987844816764311E-007,  3.395386910695348E-008,  1.473591517138764E-008),
            (0.186352453867878     ,  0.886697444462921     ,  0.384664372898837     ),
        )),
        ((20000,    0), (
            (1.041981622536972E-007,  1.530625383237532E-007,  6.638956883364688E-008),
            (0.849303560409244     , -0.499615987399218     , -0.216598783596960     ),
            (1.042587368663485E-007,  1.530945542165361E-007,  6.640215019914907E-008),
            (0.851387989281649     , -0.501002655592013     , -0.217329129993477     ),
        )),
        ((30000, 1950), (
            (-1.951094237840882E-007, -4.935428975279746E-008, -2.139901342403526E-008),
            (-0.265612225902353     ,  0.863968828300309     ,  0.374891214581348     ),
            (-1.951867950737523E-007, -4.928726894552656E-008, -2.136835626950668E-008),
            (-0.261529345669153     ,  0.869613400114242     ,  0.377162243664278     ),
        )),
        ((30000, 2050), (
            (-1.937399784367661E-007, -5.370217577070683E-008, -2.328836650985934E-008),
            (-0.288493718866083     ,  0.857773132949370     ,  0.372198925520654     ),
            (-1.938191231536331E-007, -5.363690503438287E-008, -2.325846983835394E-008),
            (-0.284560327782760     ,  0.863507337974735     ,  0.374508904388420     ),
        )),
        ((45000,    0), (
            (-1.540185537368625E-007, -1.200065354747816E-007, -5.203462221605963E-008),
            (-0.635950307873711     ,  0.689573999832052     ,  0.298714485895080     ),
            (-1.539719292367443E-007, -1.200873798187842E-007, -5.207026450573971E-008),
            (-0.643670370381919     ,  0.684339853011116     ,  0.296734862846313     ),
        )),
        ((45000, 1950), (
            (-1.550368369607363E-007, -1.188981579399755E-007, -5.155281354798770E-008),
            (-0.630053480028084     ,  0.694114319455247     ,  0.300688149490939     ),
            (-1.549909048771873E-007, -1.189793342233356E-007, -5.158860013070839E-008),
            (-0.637817020965380     ,  0.688935702092307     ,  0.298732664944296     ),
        )),
    )
    for testInput, expectedOutput in testData:
        actualOutput = evp(*testInput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-7):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
