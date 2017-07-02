Installation and Setup
======================

Sen2Three is completely written in Python 2.7. It will support the three following Operating Systems:

* Linux,
* Mac OSX,
* Windows,

(64 bit is mandatory).

The installation of the whole system is performed in two steps:

* Installation or upgrade of the Anaconda Runtime Environment
* Installation of the Processor itself.

.. _Anaconda2: https://www.continuum.io/why-anaconda

The Sen2Three application works under the umbrella of the Anaconda (Python 2.7) distribution package. It is built using
the Anaconda2 V.4.0 Development and Runtime Environment. A detailled description can be found here: (Anaconda2_).

Anaconda Upgrade
----------------
If you have already installed Anaconda on you platform, due to an installation of Sen2Cor, no further action is
necessary. If your Anaconda version should be updated, you can perform the following command via the command line::

    C:\>conda update conda
    Using Anaconda Cloud api site https://api.anaconda.org
    Fetching package metadata: ....

Should end with displaying the following information::

    conda                     4.0.5                    py27_0

    C:\>conda update anaconda
    Using Anaconda Cloud api site https://api.anaconda.org
    Fetching package metadata: ....

Should end with displaying the following information::

    anaconda                  4.0.0               np110py27_0

Then, check the proper installation with::

    C:\>python
    Python 2.7.11 |Anaconda 4.0.0 (64-bit)| (default, Feb 16 2016, 09:58:36) [MSC v.1500 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    Anaconda is brought to you by Continuum Analytics.
    Please check out: http://continuum.io/thanks and https://anaconda.org

You then can skip the next section and continue with the setup of Sen2Three.

Anaconda Installation from Scratch
----------------------------------
If you never installed Anaconda before, then follow the steps below:

Download the recent version of the Anaconda python distribution for your operating system from:
http://continuum.io/downloads and install it according to the default recommendations of the anaconda installer.
It is strongly recommended to choose a local installation, except if you have the full administrator
rights on your machine.

At the end of the installation, open a command line window and check the proper installation by typing “python.”
It should display::

    C:\>python
    Python 2.7.11 |Anaconda 4.0.0 (64-bit)| (default, Feb 16 2016, 09:58:36) [MSC v.1500 64 bit (AMD64)] on win32
    Type "help", "copyright", "credits" or "license" for more information.
    Anaconda is brought to you by Continuum Analytics.
    Please check out: http://continuum.io/thanks and https://anaconda.org

Deinstallation of an old Sen2Three installation
-----------------------------------------------
A deinstallation of an existing sen2three installation can be performed with::

    C:\Users\<local_user>>pip uninstall sen2three
    Uninstalling sen2three-1.0.0:
      c:\users\<local_user>\appdata\local\continuum\anaconda2\lib\site-packages\sen2three-1.0.1-py2.7.egg
      c:\users\<local_user>\appdata\local\continuum\anaconda2\scripts\l3_process-02.02.06-script.py
      c:\users\<local_user>\appdata\local\continuum\anaconda2\scripts\l3_process-02.02.06.exe
      c:\users\<local_user>\appdata\local\continuum\anaconda2\scripts\l3_process-1.0.1-script.py
      c:\users\<local_user>\appdata\local\continuum\anaconda2\scripts\l3_process-1.0.1.exe
      c:\users\<local_user>\appdata\local\continuum\anaconda2\scripts\l3_process-script.py
      c:\users\<local_user>\appdata\local\continuum\anaconda2\scripts\l3_process.exe

    Proceed (y/n)? y
      Successfully uninstalled sen2three-1.0.1

If you have multiple Sen2Three versions installed, you can repeat the command until no further installations are found.

Sen2Three Installation
----------------------
For Windows:

Download the zip archive from http://step.esa.int/main/third-party-plugins-2/sen2three and extract it with an unzip utility.
Open a command line window and change the directory
to the location where you have extracted the archive. Step into the folder sen2three-1.1.0, type::

    python setup.py install

and follow the instructions. The setup will install the Sen2Three application and all its dependencies under the
site-packages folder of the Anaconda python distribution. At the end of the installation you can select your home
directory for the Sen2Three configuration data. This is by default::

    ”C:\Users\<your user account>\documents\sen2three”

The setup script generates the following two environment variables:

* SEN2THREE_HOME : this is the directory where the user configuration data are stored (see above). This can be changed later by you in setting the environment variable to a different location.
* SEN2THREE_BIN : this is a pointer to the installation of the Sen2Three package. This is located in the “site-packages” folder of Anaconda. Do not change this.

Open a new command line window, to be secure that your new environment settings are updated.
From this new command line window perform the test below. This will give you a list of possible options::

    C:\>L3_Process --help
    usage: L3_Process.py [-h] [--resolution {10,20,60}] [--clean] directory

    Sentinel-2 Level 3 Prototype Processor (SEN2THREE), 1.1.0, created:
    2017.07.01, supporting Level-1C product version: 14.

    positional arguments:
      directory             Directory where the Level-2A input files are located

    optional arguments:
      -h, --help            show this help message and exit
      --resolution {10,20,60}
                            Target resolution, can be 10, 20 or 60m. If omitted,
                            all resolutions will be processed
      --clean               Removes the L3 product in the target directory before
                            processing. Be careful!

    This will give you a list of possible further options how to operate.
    If no errors are displayed, your installation was successful.

If no errors are displayed, your installation was successful.

For Linux and Mac:

Download the archive from http://step.esa.int/main/third-party-plugins-2/sen2three, and extract it with::

    tar –xvzf sen2three-1.1.0.tar.gz

Open a shell, change the directory to the new created folder sen2three-1.1.0, type::

    python setup.py install

and follow the instructions. The setup will install the Sen2Three application and all its dependencies under the
site-packages folder of the Anaconda python distribution. At the end of the installation you can select your home
directory for the Sen2Three configuration data. By default this is the directory where your $HOME environment
variable points to. The setup script generates a script called “L3_Bashrc” and places it into the sen2three folder
at your home directory. It contains the following two environment variables:

* SEN2THREE_HOME : this is the directory where the user configuration data are stored (see above). This can be changed later by you in setting the environment variable to a different location.
* SEN2THREE_BIN : this is a pointer to the installation of the Sen2Three package. This is located in the“site-packages” folder of the anaconda installation. Do not change this.

These settings are necessary for the execution of the processor. There are two possibilities how you can finish the setup:

* You can call this script automatically via your .bashrc or .profile script (OS dependent). For this purpose, add the line “source <location of your script>/L3_Bashrc” to your script.
* You can call this script also manually via “source L3_Bashrc” every time before starting the processor. However this is not recommended, as it may be forgotten.

Finally, to check the installation after sourcing the L3_Bashrc, call the processor via::

    C:\>L3_Process --help
    usage: L3_Process.py [-h] [--resolution {10,20,60}] [--clean] directory

    Sentinel-2 Level 3 Prototype Processor (SEN2THREE), 1.1.0, created:
    2017.07.01, supporting Level-1C product version: 14.

    positional arguments:
      directory             Directory where the Level-2A input files are located

    optional arguments:
      -h, --help            show this help message and exit
      --resolution {10,20,60}
                            Target resolution, can be 10, 20 or 60m. If omitted,
                            all resolutions will be processed
      --clean               Removes the L3 product in the target directory before
                            processing. Be careful!

    This will give you a list of possible further options how to operate.
    If no errors are displayed, your installation was successful.
