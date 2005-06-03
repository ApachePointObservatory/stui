#!/usr/local/bin/python
import Numeric
import RO.PhysConst
import RO.MathUtil
from RO.Astro import llv

# Constants
# mi is the J2000-to-B1950 conversion matrix.
_MatPP = Numeric.array((
	(+0.999925679499910E+00, +0.111814828407820E-01, +0.485900388918300E-02), 
	(-0.111814827888050E-01, +0.999937484898031E+00, -0.271771435010000E-04), 
	(-0.485900400882800E-02, -0.271557449570000E-04, +0.999988194601879E+00),
))
_MatPV = Numeric.array((
	(-0.499964934869971E+02, -0.559089812357749E+00, -0.242926766692029E+00), 
	(+0.559089812357749E+00, -0.499970836518607E+02, +0.135817124321463E-02), 
	(+0.242926766692029E+00, +0.135827437561775E-02, -0.499996194095093E+02), 
))
_MatVP = Numeric.array((
	(-0.262594869133001E-10, +0.115343249718602E-07, -0.211428197209230E-07), 
	(-0.115367740825326E-07, -0.128994690726957E-09, +0.594324870437638E-09), 
	(+0.211484570051212E-07, -0.413913981487726E-09, +0.102735197319772E-09), 
))
_MatVV = Numeric.array((
	(+0.999904322043106E+00, +0.111814516089680E-01, +0.485851959050100E-02), 
	(-0.111814516010690E-01, +0.999916125340107E+00, -0.271658666910000E-04), 
	(-0.485851960868600E-02, -0.271626143550000E-04, +0.999966838131419E+00),
))

def fk4FromICRS (icrsP, icrsV, fk4Epoch):
	"""
	Converts mean fk4 equatorial coordinates to ICRS coordinates.
	Uses the approximation that ICRS is FK5 J2000.
	
	Inputs:
	- icrsP(3)	ICRS cartesian position (au)
	- icrsV(3)	ICRS cartesian velocity (au per Julian year),
				i.e. proper motion and radial velocity
	- fk4Epoch	date of fk4 coordinates (Besselian epoch)
				note: tdt will always do and utc is usually adequate
	
	Returns a tuple containing:
	- fk4P(3)	FK4 cartesian position (au), a Numeric.array
    - fk4V(3)	FK4 cartesian velocity (au/Besselian year), a Numeric.array
	
	Error Conditions:
	none
	
	Warnings:
	The FK4 system refers to a specific set of precession constants,
	and not all Besselian-epoch data was precessed using these constants
	(especially data for epochs before B1950).
	
	Details:
	One approximation is used:
	- Velocity is not corrected for time-variation in the e-terms.
	This introduces errors on the order of a milliarcsecond per century.
	
	References:
	P.T. Wallace's FK524 routine
	
	History:
	2002-07-22 ROwen  Converted to Python from the TCC's cnv_J2FK4 4-1.
	"""
	eTerms = llv.etrms (fk4Epoch)
	precMat = llv.prebn (1950.0, fk4Epoch)

	#  convert position and velocity from J2000.0 to B1950
	b1950P = Numeric.matrixmultiply(_MatPP, icrsP) + Numeric.matrixmultiply(_MatPV, icrsV)
	b1950V = Numeric.matrixmultiply(_MatVP, icrsP) + Numeric.matrixmultiply(_MatVV, icrsV)

	#  correct position for velocity (pm and rad. vel.) to fk4Epoch
	tempP = b1950P + b1950V * (fk4Epoch - 1950.0)

	#  precess position and velocity to B1950
	meanFK4P = Numeric.matrixmultiply (precMat, tempP)
	fk4V     = Numeric.matrixmultiply (precMat, b1950V)

	#  add e-terms to mean position, iterating thrice (should be plenty!)
	#  to get mean catalog place. As a minor approximation,
	#  we don't bother to add variation in e-terms to the velocity.
	fk4P = meanFK4P.copy()
	for iterNum in range(3):
		magP = RO.MathUtil.vecMag(fk4P)
		fk4P = meanFK4P + eTerms * magP

	return (fk4P, fk4V)


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing fk4FromICRS"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(((1000000, 2000000, 3000000), (40, 50, 60), 1900), 
		(
			(1069386.58330499, 1971912.61861982, 2983962.16684203), 
			(41.6474766458155, 49.0762712755130, 59.6226168717454), 
		)), 
		(((1000000, 2000000, 3000000), (40, 50, 60), 1950), 
		(
			(1034817.19162690, 1986133.35354100, 2992060.55876499), 
			(40.8063705688967, 49.5369064621085, 59.8229402074541), 
		)), 
		(((1000000, 2000000, 3000000), (40, 50, 60), 2000), 
		(
			(1000006.10371259, 1999992.73518705, 2999999.24980262), 
			(39.9590997929001, 49.9882461779056, 60.0191198178096), 
		)), 
		(((1000000, 2000000, 3000000), (40, 50, 60), 2050), 
		(
			(964957.773846676, 2013487.38484989, 3007776.94049935), 
			(39.1057861748448, 50.4302164717177, 60.2111277935353), 
		)), 
		(((1000000, 0000000, 3000000), (40, 50, 0), 2050), 
		(
			(987319.340838269, 13612.5191582164, 3004831.47188928), 
			(39.3740636811606, 50.4315879360190, 0.213720412393103), 
		)), 
		(((1000000, 2000000, 0000000), (40, 0, 60), 2050), 
		(
			(979561.307549451, 2011069.64299352, 7812.64314911968), 
			(39.7279255440172, 0.434041277919628, 60.2127912563316), 
		)), 
		(((1000000, 2000000, -3000000), (40, 50, 60), 2050), 
		(
			(994104.121533616, 2013650.26088093, -2992152.26369430), 
			(39.2326911081840, 50.4294872409111, 60.2117440729014), 
		)), 
		(((-1000000, -2000000, -3000000), (40, 50, 60), 2050), 
		(
			(-961055.310507727, -2008446.11637694, -3001759.18274008), 
			(39.1864874821973, 50.4520451075325, 60.1706545088932), 
		)), 
		(((-1000000, -2000000, -3000000), (-40, 50, -60), 2050), 
		(
			(-965025.701555348, -2008490.64962644, -3007778.25408874), 
			(-40.2231599798504, 49.5614046850719, -60.2138384397619), 
		)), 
	)
	for testInput, expectedOutput in testData:
		actualOutput = fk4FromICRS(*testInput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
