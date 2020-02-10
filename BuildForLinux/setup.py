"""This script builds a runstui.spec file that can be sent to pyinstaller. It is
a system agnostic way to install STUI. This file takes one argument, a path to
RO, opscore, actorcore, and all the other essential libraries for STUI.
pyinstaller can use runstui.spec to build a version of STUI that doesn't require
a python interpreter. It's  possible that this will also speed up stui versus
using an interpreter, but that is untested. Check README.md for build
instructions.
"""

import sys
from pathlib import Path

# Create useful paths
build_dir = Path('__main__').parent.absolute()
print(build_dir)
repo = build_dir.parent
print(repo)
tui_dir = repo / 'TUI'
print(tui_dir)
executable = repo / 'runstui.py'
print(executable)

data_added = []  # A list of tuples of files/directories to be added in install
# This is a place to look for non-python requirements, we need a relative path
# for them

# TODO This is very inflexible and requires the user to be in the build_dir
# TODO This requires all software to be in the same directory in sys.argv[1]
data_added.append(('../TUI/Sounds/', 'TUI/Sounds/'))
data_added.append(('../TUI/Scripts/', 'TUI/Scripts/'))
data_added.append(('../TUI/Models/', 'TUI/Models/'))

# print(sys.argv)
# Checks sys.argv for RO path
try:
    software_dir = Path(sys.argv[1])
except IndexError:
    raise Exception('Please provide a path to software (RO, opscore, actorcore'
                    ' etc.)')

try:
    rel_software = software_dir.relative_to(build_dir)
except ValueError:
    levels_up = '..'
    for parent in build_dir.parents:
        print(parent)
        try:
            rel_software = software_dir.relative_to(parent)
            break
        except ValueError:
            levels_up += '/..'
    rel_software = levels_up / rel_software
print(rel_software)

# Include all the necessary paths of non-python stuff (and a few pythons like
# cmds.py. Not sure why cmds.py isn't included normally, but I think it has to
# do with how it is imported using imp (in opscore/protocol/keys.py)
bitmaps_rel = rel_software / 'RO/python/RO/Bitmaps/'
data_added.append((str(bitmaps_rel), 'RO/Bitmaps/'))
print(bitmaps_rel)
opscore_rel = rel_software / 'opscore/trunk/python/opscore/'
data_added.append((str(opscore_rel), 'opscore/'))
print(opscore_rel)
actorkeys_rel = rel_software / 'actorkeys/trunk/python/actorkeys/'
data_added.append((str(actorkeys_rel), 'actorkeys/'))
print(actorkeys_rel)
plc_rel = rel_software / 'plc/trunk/python/plc/'
if not plc_rel.exists():
    plc_rel = rel_software / 'plc/python/plc/'
data_added.append((str(plc_rel), 'plc/'))
print(plc_rel)
plc_root_rel = rel_software / 'plc/trunk/'
if not plc_root_rel.exists():
    plc_root_rel = rel_software / 'plc/'
data_added.append((str(plc_root_rel), 'plc/'))
print(plc_root_rel)


# print(data_added)
spec_file = Path(repo/'BuildForLinux/runstui.spec').open('w')
spec_file.write('# -*- mode: python ; coding: utf-8 -*-\n\n')
spec_file.write('block_cipher = None\n\n\n')
spec_file.write("a = Analysis(['../runstui.py'],\n")
spec_file.write("             pathex=['{}'],\n".format(build_dir))
spec_file.write("             binaries=[],\n")
spec_file.write("             datas={},\n".format(data_added))
spec_file.write("             hiddenimports=[],\n")
spec_file.write("             hookspath=[],\n")
spec_file.write("             runtime_hooks=[],\n")
spec_file.write("             excludes=[],\n")
spec_file.write("             win_no_prefer_redirects=False,\n")
spec_file.write("             win_private_assemblies=False,\n")
spec_file.write("             cipher=block_cipher,\n")
spec_file.write("             noarchive=False)\n")
spec_file.write("pyz = PYZ(a.pure, a.zipped_data,\n")
spec_file.write("             cipher=block_cipher)\n")
spec_file.write("exe = EXE(pyz,\n")
spec_file.write("          a.scripts,\n")
spec_file.write("          [],\n")
spec_file.write("          exclude_binaries=True,\n")
spec_file.write("          name='runstui',\n")
spec_file.write("          debug=False,\n")
spec_file.write("          bootloader_ignore_signals=False,\n")
spec_file.write("          strip=False,\n")
spec_file.write("          upx=True,\n")
spec_file.write("          upx_exclude=[],\n")
spec_file.write("          runtime_tmpdir=None,\n")
spec_file.write("          console=True,\n")
spec_file.write("          icon='STUI.icns')\n")
spec_file.write("coll = COLLECT(exe,\n")
spec_file.write("               a.binaries,\n")
spec_file.write("               a.zipfiles,\n")
spec_file.write("               a.datas,\n")
spec_file.write("               strip=False,\n")
spec_file.write("               upx=True,\n")
spec_file.write("               upx_exclude=[],\n")
spec_file.write("               name='runstui')\n")
