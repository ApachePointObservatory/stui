#!/usr/bin/env python
"""Test code to try out ideas for reading a catalog and checking it.

To Do:
- Check values; this will require <<EntryError>> handler
- Modify code somewhere so setting menu items, checkboxes, etc. is not case-or-abbrev-sensitive.
"""
import RO.Wdg
import TUI.Base.Wdg
import TUI.Models.TUIModel
from CatalogMenuWdg import CatalogMenuWdg
from TUI.TCC.SkyWindow import SkyWdg

tuiModel = TUI.Models.TUIModel.Model(True)

root = tuiModel.tkRoot

sw = SkyWdg(root)
sb = RO.Wdg.StatusBar(root)
c = CatalogMenuWdg(root, statusBar=sb)

sw.pack(expand=True, fill="both")
sb.pack(expand=True, fill="x")
c.pack()

tuiModel.reactor.run()
