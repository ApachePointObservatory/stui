#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-01-12
# @Filename: Actorkeys.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import shutil
import os
import tempfile
from io import BytesIO
from urllib import urlopen
from zipfile import ZipFile


__all__ = ['refreshActorkeys', 'getSTUIPath', 'getActorkeysPath']


def getSTUIPath():
    """Returns a valid path for STUI configuration in the home directory."""

    return os.path.expanduser('~/.stui/')


def getActorkeysPath():
    """Returns the actorkeys path."""

    return os.path.join(getSTUIPath(), 'actorkeys')


def refreshActorkeys():
    """Refreshes the internal copy of actorkeys."""

    # Get temporary file
    tmp_path = tempfile.gettempdir()
    uncompress_path = os.path.join(tmp_path, 'actorkeys-sdss5')

    if os.path.exists(uncompress_path):
        shutil.rmtree(uncompress_path)

    # Download from GitHub
    resp = urlopen("https://github.com/sdss/actorkeys/archive/refs/heads/sdss5.zip")
    myzip = ZipFile(BytesIO(resp.read()))
    myzip.extractall(path=tmp_path)

    stui_path = getSTUIPath()
    actorkeys_path = getActorkeysPath()
    if os.path.exists(actorkeys_path):
        shutil.rmtree(actorkeys_path)

    shutil.copytree(os.path.join(uncompress_path, 'python', 'actorkeys'),
                    actorkeys_path)
