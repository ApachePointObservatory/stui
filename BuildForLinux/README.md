# Pyinstaller for STUI
Written by Dylan Gatlin, 2019-10-5

This tool is meant to help Linux users produce a built version of STUI that is
more usable than working with Python source code. It can be run using a few
simple lines

## Dependencies
I recommend you use a clean environment and install all necessary dependencies specifically for this.
```bash
# Create an environment
conda create -n tui27 python=2.7 numpy matplotlib pyinstaller pillow tk pathlib astropy pathlib twisted
conda activate tui27
pip install pygame pyfits

# Collect non-standard dependencies
mkdir ~/software
cd ~/software
git clone https://github.com/ApachePointObservatory/RO  # Make sure all dependencies are in this parent directory
svn co https://svn.sdss.org/repo/operations/general/external/trunk external/trunk --username=<wiki-user>
svn co https://svn.sdss.org/repo/operations/general/actorkeys/trunk actorkeys/trunk --username=<wiki-user>
svn co https://svn.sdss.org/repo/operations/general/actorcore/trunk actorcore/trunk --username=<wiki-user>
svn co https://svn.sdss.org/repo/operations/general/opscore/trunk opscore/trunk --username=<wiki-user>
git clone https://github.com/ApachePointObservatory/stui  # This can be anywhere, as long as you build from inside it
git clone https://github.com/StarkillerX42/plc
```

### Add these items to your bashrc/bash_profile

```bash
export SOFTWAREDIR=~/software
export PYTHONPATH=$SOFTWAREDIR/actorcore/trunk/python/:$PYTHONPATH
export PYTHONPATH=$SOFTWAREDIR/actorkeys/trunk/python/:$PYTHONPATH
export PYTHONPATH=$SOFTWAREDIR/external/trunk/python/:$PYTHONPATH
export PYTHONPATH=$SOFTWAREDIR/opscore/trunk/python/:$PYTHONPATH
export PYTHONPATH=$SOFTWAREDIR/plc/trunk/python/:$PYTHONPATH
export PYTHONPATH=$SOFTWAREDIR/RO/python/:$PYTHONPATH
```

## Building

```cd stui/BuildForLinux
# Create a .spec file used for building
python setup.py /home/<username>/software/RO
# build into .dist
pyinstaller runtui.spec
# Move dist to a permanent location
sudo mv dist/ /etc/STUI/
```

## Creating a shortcut

If you follow each of these lines exactly, you will have made an executable, equipped with all its necessary
dependencies at /etc/STUI/runtui/runtui

You will also need to make a bash script to initialize TUI. I recommend you put
that in /usr/bin/local/tui or your desktop. If you choose to do your Desktop, there is an .ico file you can add to give
it an image for the icon.

```
#!/bin/sh
/etc/STUI/runtui/runtui
```

Then add execute permissions

````
sudo chmod a+x /usr/bin/local/tui
````