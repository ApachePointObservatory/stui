#!/usr/local/bin/python
"""Model for guide cameras.

2005-01-28 ROwen	preliminary; has all existing keywords, but there will be more
					and "star" will probably change to include ellipticity.
2005-02-23 ROwen	added expTime and thresh.
"""
__all__ = ['getModel']

import RO.CnvUtil
import RO.KeyVariable
import TUI.TUIModel

class _GCamInfo:
	"""Exposure information for a camera
	
	Inputs:
	- min/maxExpTime: minimum and maximum exposure time (sec)
	- slitViewer: True if a slit viewer
	"""
	def __init__(self,
		minExpTime = 0.1,
		maxExpTime = 3600,
		slitViewer = False,
	):
		self.minExpTime = float(minExpTime)
		self.maxExpTime = float(maxExpTime)
		self.slitViewer = bool(slitViewer)

# dictionary of instrument information
# instrument names should be lowercase
_GCamInfoDict = {
	"gcam": _GCamInfo(
	),
	"ecam": _GCamInfo(
		slitViewer = True,
	),
	"dcam": _GCamInfo(
		slitViewer = True,
	),
}

# cache of guide camera models
# each entry is gcamName: model
_modelDict = {}

def getModel(gcamName):
	global _modelDict
	gcamNameLow = gcamName.lower()
	model = _modelDict.get(gcamNameLow)
	if model == None:
		model = Model(gcamName)
		_modelDict[gcamNameLow] = model
	return model

class Model (object):
	def __init__(self, gcamName):
		self.gcamName = gcamName
		self.actor = gcamName.lower()

		self.gcamInfo = _GCamInfoDict[self.actor]
		
		self.tuiModel = TUI.TUIModel.getModel()
		
		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = self.actor,
			dispatcher = self.tuiModel.dispatcher,
			converters = str,
			allowRefresh = True,
		)

		self.cradius = keyVarFact(
			keyword="cradius",
			converters = float,
			description="Centroid radius (unbinned pixels)",
		)
		
		self.expTime = keyVarFact(
			keyword="time",
			converters = float,
			description="Exposure time (sec)",
		)

		self.guiding = keyVarFact(
			keyword="guiding",
			converters = RO.CnvUtil.asBool,
			description="True if guiding; False otherwise",
		)

		self.imgFile = keyVarFact(
			keyword="imgFile",
			description="Path to new guide camera image",
			allowRefresh = False,
		)

		self.maskFile = keyVarFact(
			keyword="maskFile",
			description="Path to mask that matches imgFile",
			allowRefresh = False,
		)

		self.star = keyVarFact(
			keyword="star",
			converters = (int,) + (float,)*10 + (int, float),
			description="""Data about a star. The fields are as follows:
(this is a guess as of 2005-01-31; fields may change!)
1.  	index: an index identifying the star within the list of stars returned by the command.
2,3.  	x,yCenter: centroid (binned pixels)
4,5.  	x,yError: estimated standard deviation of x,yCenter (binned pixels)
6		radius: radius of centroid region
7.  	asymmetry: a measure of the asymmetry of the object;
		the value minimized by PyGuide.centroid.
		Warning: not normalized, so probably not much use.
8.  	FWHM
9,		ellipticity
10		ellMajAng: angle of ellipse major axis in x,y frame
11.  	chiSq: goodness of fit to model star (a double gaussian). From PyGuide.starShape.
12.  	counts: sum of all unmasked pixels within the centroid radius (ADUs). From PyGuide.centroid
13.  	background: background level of fit to model star (ADUs). From PyGuide.starShape
14.  	amplitude: amplitude of fit to model star (ADUs). From PyGuide.starShape
""",
			nval = 14,
			allowRefresh = False,
		)
		
		self.thresh = keyVarFact(
			keyword="thresh",
			converters = float,
			description="Findstars threshold (sigma)",
		)
		
		keyVarFact.setKeysRefreshCmd(getAllKeys=True)


if __name__ == "__main__":
#	getModel("dcam")
	getModel("ecam")
	getModel("gcam")
