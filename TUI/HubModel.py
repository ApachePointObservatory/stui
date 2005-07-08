#!/usr/local/bin/python
"""An object that models the current state of the Hub.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

2004-07-22 ROwen
2004-08-25 ROwen	Added users (a new hub keyword) and commented out commanders.
"""
import RO.CnvUtil
import RO.CoordSys
import RO.KeyVariable
import TUI.TUIModel

_theModel = None

def getModel():
	global _theModel
	if _theModel ==  None:
		_theModel = _Model()
	return _theModel

class _Model (object):
	def __init__(self,
	**kargs):
		self.actor = "hub"
		self.dispatcher = TUI.TUIModel.getModel().dispatcher
		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = self.actor,
			converters = str,
			nval = (0,None),
			dispatcher = self.dispatcher,
		)

		self.actors = keyVarFact(
			keyword = "Actors",
			description = "list of current actors",
		)
		
#		self.commanders = keyVarFact(
#			keyword = "Commanders",
#			description = "list of current commanders (users plus various hub tasks)",
#		)
		
		self.users = keyVarFact(
			keyword = "Users",
			description = "list of current human (non-hub) commanders",
		)

		self.httpRoot = keyVarFact(
			keyword = "HTTPRoot",
			nval = 2,
			description = "image http info: host, root dir",
		)

		keyVarFact.setKeysRefreshCmd()

if __name__ ==  "__main__":
	# confirm compilation
	model = getModel()
