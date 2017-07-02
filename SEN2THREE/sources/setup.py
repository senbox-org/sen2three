#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
# Sen2Three setup script
# 
# usage: 
# to build distribution for windows:
# 	'python setup.py sdist --formats=zip'
# else:
# 	'python setup.py sdist --formats=gztar'
# to install at target system:
#	'python setup.py install' and follow the instructions ...
#

from setuptools import setup, find_packages
from distutils.dir_util import mkpath
from shutil import copyfile
import os, sys, platform

name = 'sen2three'
#
# This needs to be changed with each new version:
#------------------------------------------------
version = '1.1.0'
longVersion = '01.01.00'
#
# Do not change anything below:
#----------------------------------------------------------------------------
consoleScript1 = 'L3_Process = sen2three.L3_Process:main'
consoleScript2 = 'L3_Process-' + version + ' = sen2three.L3_Process:main'
consoleScript3 = 'L3_Process-' + longVersion + ' = sen2three.L3_Process:main'

L3_Process = 'L3_Process'
L3_Process_Version = L3_Process + '-' + version

def copyConfiguration():
    sys.stdout.write('\nSen2Three ' + version + ' setup script:\n')
    sys.stdout.write('This will finish the configuration of the environment settings.\n')
    user_input = raw_input('\nOK to continue? [y/n]: ')
    if user_input == 'n':
        return False

    cfgfl3 = 'L3_GIPP.xml'
    srcfl3 = os.path.join(modulefolder, os.path.join('cfg', cfgfl3))
    SEN2THREE_HOME = os.path.join(cfghome, 'sen2three')
    break_condition = True
    while True:
        sys.stdout.write('\nPlease input a path for the sen2three home directory:\n')
        sys.stdout.write('default is: ' + SEN2THREE_HOME + '\n')
        user_input = raw_input('Is this OK? [y/n]: ')
        if user_input == 'n':
            SEN2THREE_HOME = raw_input('New path: ')
            sys.stdout.write('New path is: ' + SEN2THREE_HOME +'\n')
            user_input = raw_input('Is this OK? [y/n]: ')
            if user_input == 'y':
                break_condition = True
            else:
                break_condition = False
        else:
            break_condition = True

        if break_condition:
            os.environ['SEN2THREE_HOME'] = SEN2THREE_HOME
            L3_cfg = os.path.join(SEN2THREE_HOME, 'cfg')
            mkpath(L3_cfg)
            copyfile(srcfl3, os.path.join(L3_cfg, cfgfl3))
            break

    sys.stdout.write('Setting environment for sen2three ...\n')
    if system == 'Windows':
        # setting the environments for the application under Windows:
        try:
            setSEN2THREE_HOME = 'setx SEN2THREE_HOME ' + SEN2THREE_HOME
            sys.stdout.write('Setting environment variable SEN2THREE_HOME:')
            os.system(setSEN2THREE_HOME)
            setSEN2THREE_BIN = 'setx SEN2THREE_BIN ' + modulefolder
            sys.stdout.write('Setting environment variable SEN2THREE_BIN:')
            os.system(setSEN2THREE_BIN)
        except:
            sys.stderr.write('Error in environment settings!\n')
            sys.exit(-1)
        sys.stdout.write('Congratulations, you are done!\n')
    else:
        # setting the environments for the application into L3_Bashrc (Linux and MacOSX):
        L3_Bashrc = '#!/usr/bin/env bash\n'
        L3_Bashrc += '# BEGIN\n'
        L3_Bashrc += '# Sen2Three environmental setup, version ' + version +'\n'
        L3_Bashrc += '# settings automatically generated by setup.py\n'
        L3_Bashrc += '# source this script either manually via: "source L3_Bashrc"\n'
        L3_Bashrc += '# or call it from your .bashrc or .profile script\n#\n'
        if system == 'Darwin':
            L3_Bashrc += 'export LC_ALL=en_US.UTF-8\n'
            L3_Bashrc += 'export LANG=en_US.UTF-8\n'
        L3_Bashrc += 'export SEN2THREE_HOME=' + SEN2THREE_HOME + '\n'
        L3_Bashrc += 'export SEN2THREE_BIN=' + modulefolder + '\n'
        L3_Bashrc += '# END\n'
        sys.stdout.write('Creating L3_Bashrc script under:\n' + SEN2THREE_HOME + '\n')
        try:
            textFile = open(SEN2THREE_HOME + '/L3_Bashrc', 'w')
            textFile.write(L3_Bashrc)
            textFile.close()
        except:
            sys.stderr.write('Cannot create the L3_Bashrc script under:\n' + SEN2THREE_HOME + '\n')
            sys.exit(-1)
        # creating the L3_Process.bash script:
        CONDA_BIN = sys.prefix + '/bin'
        L3_Process_bash = '#!/usr/bin/env bash\n'
        L3_Process_bash += '# BEGIN\n'
        L3_Process_bash += '# Sen2Three L3_Process.bash, version ' + version +'\n'
        L3_Process_bash += '# settings automatically generated by setup.py\n#\n'
        L3_Process_bash += 'export PATH=' + CONDA_BIN + ':$PATH\n'
        L3_Process_bash += 'source ./L3_Bashrc\n'
        L3_Process_bash += 'L3_Process-$1 $2 $3 $4\n'
        L3_Process_bash += '# END\n'
        sys.stdout.write('Creating L3_Process.bash script under:\n' + SEN2THREE_HOME + '\n')
        try:
            textFile = open(SEN2THREE_HOME + '/L3_Process.bash', 'w')
            textFile.write(L3_Process_bash)
            textFile.close()
        except:
            sys.stderr.write('Cannot create the L3_Process.bash script under:\n' + SEN2THREE_HOME + '\n')
            sys.exit(-1)

        # create the glymur configuration file for OpenJPEG2:
        glymurrc = '[library]\n'
        glymurrc += 'openjp2: ' + libOpj2Target + '\n'
        glymurrcPath = os.path.join(cfghome, '.config', 'glymur')
        glymurrcFile = os.path.join(glymurrcPath, 'glymurrc')
        sys.stdout.write('Creating the configuration file for OpenJPEG2 under:\n' + glymurrcPath + '\n\n')
        try:
            mkpath(glymurrcPath)
        except:
            sys.stdout.write('Path already exists ...')
        try:
            textFile = open(glymurrcFile, 'w')
            textFile.write(glymurrc)
            textFile.close()
        except:
            sys.stderr.write('Cannot create the configuration file for OpenJPEG2 under:\n ' + glymurrcPath + '\n\n')
            return False

        sys.stdout.write('Congratulations, you are nearly done ...\n')
        sys.stdout.write('Last step: cd to ' + SEN2THREE_HOME + ',\n')
        sys.stdout.write('source the <L3_Bashrc> script either manually via: "source L3_Bashrc"\n')
        sys.stdout.write('or integrate this call in your .bashrc or .profile script. Afterwards,\n')

    sys.stdout.write('- you can call the processor from everywhere via: "L3_Process"\n')
    sys.stdout.write('- you will find the default configuration called "L3_GIPP.xml" under:\n' + L3_cfg + '\n\n')
    return True

setup(
    name = name,
    version = version,
    description = 'Sen2three: Sentinel 3 Spatio Temporal Processor',
    long_description = open('README.md').read(),
    packages=find_packages(),
    include_package_data=True,
    platforms=['linux-x86_64', 'macosx-x86_64', 'win-amd64'],
    entry_points={
        'console_scripts': [consoleScript1, consoleScript2, consoleScript3, ]
    },
    zip_safe = False,
)

try:
    sys.argv[1] == True
except:
    sys.stderr.write('argument must either be "sdist" or "install ..."\n')
    sys.exit(0)
if (sys.argv[1] != 'install'):
    sys.exit(0)

system = platform.system()
if system == 'Windows':
    prefix = os.path.join(sys.prefix, 'Lib', 'site-packages')
else:
    prefix = os.path.join(sys.prefix, 'lib', 'python2.7', 'site-packages')

modulefolder = os.path.join(prefix, name + '-' + version + '-py2.7.egg', 'sen2three')
buildfolder = os.path.join(modulefolder, 'build')

if system == 'Darwin':
    libopj2 = 'libopenjp2.dylib'
    targetfolder = os.path.join(sys.prefix, 'lib')
    try:
        cfghome =  os.environ['XDG_CONFIG_HOME']
    except:
        cfghome = os.environ['HOME']
elif system == 'Linux':
    libopj2 = 'libopenjp2.so'
    targetfolder = os.path.join(sys.prefix, 'lib')
    try:
        cfghome =  os.environ['XDG_CONFIG_HOME']
    except:
        cfghome = os.environ['HOME']
elif system == 'Windows':
    libopj2 = 'openjp2.dll'
    targetfolder = os.path.join(sys.prefix, 'Scripts')
    cfghome = os.path.join(os.environ['USERPROFILE'], 'documents')

libOpj2Target = os.path.join(targetfolder, libopj2)
try:
    sys.stdout.write('Checking if old Glymur version is installed:\n')
    import glymur.version as gv
    if gv.version == '0.8.4':
        os.system('conda remove --yes glymur')
    elif gv.version == '0.8.6':
        os.system('pip uninstall --yes glymur')
    sys.stdout.write('Old Glymur version uninstalled.\n')
except ImportError:
    sys.stdout.write('No old Glymur version found.\n')
    pass

sys.stdout.write('Now installing Glymur version 0.8.10:\n')
os.system('conda install --yes -c conda-forge glymur=0.8.10')

# better to do this manually, see SUM section uninstall:
# os.system('conda clean --yes --tarballs --index-cache --packages --source-cache')

if copyConfiguration() == True:
    sys.stdout.write('Installation sucessfully performed.\n')
else:
    sys.stdout.write('Errors during installation occurred.\n')
sys.exit(0)

if __name__ == '__main__':
    pass