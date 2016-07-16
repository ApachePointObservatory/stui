"""Makes TUI into a package, so one can import subpackages"""
FLAVOR = "APO" # default.  override in runtui.py if LCO version is wanted
__all__ = [FLAVOR]
