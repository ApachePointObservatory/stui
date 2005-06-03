#!/usr/local/bin/python
import Numeric
import RO.PhysConst
import RO.MathUtil
from RO.Astro import llv

# Constants
_MatPP = Numeric.array((
	(+0.999925678186902E+00, -0.111820596422470E-01, -0.485794655896000E-02),
	(+0.111820595717660E-01, +0.999937478448132E+00, -0.271764411850000E-04),
	(+0.485794672118600E-02, -0.271474264980000E-04, +0.999988199738770E+00),
))
_MatPV = Numeric.array ((
	(+0.499975613405255E+02, -0.559114316616731E+00, -0.242908945412769E+00), 
	(+0.559114316616731E+00, +0.499981514022567E+02, -0.135874878467212E-02), 
	(+0.242908966039250E+00, -0.135755244879589E-02, +0.500006874693025E+02),
))
_MatVP = Numeric.array((
	(-0.262600477903207E-10, -0.115370204968080E-07, +0.211489087156010E-07),
	(+0.115345713338304E-07, -0.128997445928004E-09, -0.413922822287973E-09),
	(-0.211432713109975E-07, +0.594337564639027E-09, +0.102737391643701E-09),
))
_MatVV = Numeric.array ((
	(+0.999947035154614E+00, -0.111825061218050E-01, -0.485766968495900E-02), 
	(+0.111825060072420E-01, +0.999958833818833E+00, -0.271844713710000E-04), 
	(+0.485766994865000E-02, -0.271373095390000E-04, +0.100000956036356E+01),
))

def icrsFromFK4 (fk4P, fk4V, fk4Epoch):
	"""
	Converts mean catalog FK4 equatorial coordinates to ICRS coordinates.
	Uses the approximation that ICRS is FK5 J2000.
	
	Inputs:
	- fk4Epoch	TDB date of fk4 coordinates (Besselian epoch)
				note: TDT will always do and UTC is usually adequate
	- fk4P(3)	mean catalog fk4 cartesian position (au)
	- fk4V(3)	mean FK4 cartesian velocity (au per Besselian year),
				i.e. proper motion and radial velocity
	
	Returns a tuple containg:
	- icrsP(3)	mean ICRS cartesian position (au), a Numeric.array
	- icrsV(3)	mean ICRS cartesian velocity (au/year), a Numeric.array
	
	Error Conditions:
	none
	
	Warnings:
	The FK4 date is in Besselian years.
	
	The FK4 proper motion is in au/Besselian year,
	whereas the FK5 J2000 proper motion is in au/Julian year.
	
	The FK4 system refers to a specific set of precession constants;
	not all Besselian-epoch data was precessed using these constants
	(especially data for epochs before B1950).
	
	References:
	P.T. Wallace's routine FK425
	
	History:
	2002-07-11 ROwen  Converted to Python from the TCC's cnv_FK42J 4-1.
	2004-05-18 ROwen	Stopped importing math; it wasn't used.
	"""
	fk4P = Numeric.array(fk4P)
	fk4V = Numeric.array(fk4V)

	#  compute new precession constants
	#  note: ETrms and PreBn both want Besselian date
	eTerms = llv.etrms (fk4Epoch)
	precMat = llv.prebn (fk4Epoch, 1950.0)

	#  subtract e-terms from position. As a minor approximation,
	#  we don't bother to subtract variation in e-terms from proper motion.
	magP = RO.MathUtil.vecMag(fk4P)
	meanFK4P = fk4P - (eTerms * magP)

	# correct position for velocity (PM and rad. vel.) to B1950
	tempP = meanFK4P + fk4V * (1950.0 - fk4Epoch)

	# precess position and velocity to B1950
	b1950P = Numeric.matrixmultiply(precMat, tempP)
	b1950V = Numeric.matrixmultiply(precMat, fk4V)

	# convert position and velocity to ICRS (actually FK5 J2000.0)
	icrsP = Numeric.matrixmultiply(_MatPP, b1950P) + Numeric.matrixmultiply(_MatPV, b1950V)
	icrsV = Numeric.matrixmultiply(_MatVP, b1950P) + Numeric.matrixmultiply(_MatVV, b1950V)

	return (icrsP, icrsV)


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing icrsFromFK4"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(((1000000, 2000000, 3000000), (40, 50, 60), 1900),
		(
			(   929683.244963302     ,   2026616.27886940     ,   3015395.98838120     ),
			(   38.3286807625452     ,   50.8858334065567     ,   60.3627612257013     ),
		)),
		(((1000000, 0, 0), (40, 0, 0), 1900),              
		(
			(   1003703.41007840     ,   22442.8991233262     ,   9755.09375276802     ),
			(   39.9889184862787     ,  0.905706818443208     ,  0.367459579186115     ),
		)),
		(((0, 2000000, 0), (0, 50, 0), 1900),
		(
			(  -44814.8232632364     ,   2004499.74395964     ,  -217.381652380232     ),
			(  -1.14079387796531     ,   49.9880577020497     , -3.764515028559184E-003),
		)),
		(((0, 0, 30000000), (0, 0, 60), 1900),
		(
			(  -291492.058777010     ,  -3250.24235322943     ,   30004587.8907069     ),
			(  5.158182703394798E-002, -2.061946781951834E-002,   60.0046123695534     ),
		)),
		(((-1000000, -2000000, -3000000), (-40, -50, 60), 1950),
		(
			(  -964968.174481507     ,  -2013496.57858614     ,  -3001777.31085417     ),
			(  -39.7705627092815     ,  -50.4569077377000     ,   59.8272699455138     ),
		)),
		(((1000000, -2000000, -3000000), (-40, 50, 60), 2000),
		(
			(   1000018.21231382     ,  -1999992.74401960     ,  -2999999.24417909     ),
			(  -40.0415521563411     ,   50.0134577025947     ,   59.9793839067662     ),
		)),
		(((1000000, -2000000, 3000000), (40, 50, 60), 2050),
		(
			(   990112.301515263     ,  -2013606.16505919     ,   2992172.70812960     ),
			(   40.9344740739882     ,   49.5597035007198     ,   59.7833122391920     ),
		)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = icrsFromFK4(*testInput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput



