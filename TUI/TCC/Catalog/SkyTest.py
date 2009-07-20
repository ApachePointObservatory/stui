#!/usr/bin/env python
"""Test code to try out ideas for reading a catalog and checking it.

To Do:
- Check values; this will require <<EntryError>> handler
- Modify code somewhere so setting menu items, checkboxes, etc. is not case-or-abbrev-sensitive.
"""
import RO.Wdg
import TUI.Base.Wdg
import TUI.TUIModel
from CatalogMenuWdg import CatalogMenuWdg
from TUI.TCC.SkyWindow import SkyWdg

root = RO.Wdg.PythonTk()

tuiModel = TUI.TUIModel.Model(True)

sw = SkyWdg(root)
sb = RO.Wdg.StatusBar(root)
c = CatalogMenuWdg(root, statusBar=sb)

sw.pack(expand=True, fill="both")
sb.pack(expand=True, fill="x")
c.pack()

root.mainloop()
