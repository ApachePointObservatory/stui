import TUI.Inst.DIS.DISModel
from TUI.Inst.DIS.StatusConfigInputWdg import StatusConfigInputWdg

class ScriptClass(object):
	"""Simple script to configure DIS.
	"""
	def __init__(self, sr):
		"""Display DIS configuration."""
		statusWdg = StatusConfigInputWdg(sr.master)
		statusWdg.grid(row=0, column=0)
	
	def run(self, sr):
		"""Configure DIS
		
		It is inefficient to tell DIS to move something that is already
		in the right location, so check each item before moving.
		"""
		disModel = TUI.Inst.DIS.DISModel.getModel()
	
		# settings
		turretPos = 1  # grating set 1 is typically high blue/high red
		maskID = 1
		filterID = 1  # 1 is clear
		rlambda = 7300  # in Angstroms
		blambda = 4400  # in Angstroms
	
		# notes:
		# - set turret before setting gratings to make sure that
		# disModel.cmdLambdas is for the correct turret.
		# - DIS only moves one motor at a time,
		# so the following code is about as efficient as it gets
		
		if turretPos != sr.getKeyVar(disModel.turretPos):
			yield sr.waitCmd(
				actor = "dis",
				cmdStr = "motors turret=%d" % turretPos,
			)
		
		if maskID != sr.getKeyVar(disModel.maskID):
			yield sr.waitCmd(
				actor = "dis",
				cmdStr = "motors mask=%d" % maskID,
			)
		
		if filterID != sr.getKeyVar(disModel.filterID):
			yield sr.waitCmd(
				actor = "dis",
				cmdStr = "motors filter=%d" % filterID,
			)
		
		# test against disModel.cmdLambdas, not disModel.actLambdas,
		# because the gratings cannot necessarily go *exactly* where requested
		# but do the best they can
		if blambda != sr.getKeyVar(disModel.cmdLambdas, ind=0):
			yield sr.waitCmd(
				actor = "dis",
				cmdStr = "motors b%dlambda=%d" % (turretPos, blambda),
			)
		
		if rlambda != sr.getKeyVar(disModel.cmdLambdas, ind=1):
			yield sr.waitCmd(
				actor = "dis",
				cmdStr = "motors r%dlambda=%d" % (turretPos, rlambda),
			)
