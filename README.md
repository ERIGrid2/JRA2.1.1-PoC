# JRA2.1.1-PoC
Proof of concept AC-ICT cosimulation setup from JRA2.1.1

## Installation

The code is currently only tested to build and run on Linux.

The following prerequisites need to be installed in order to compile and run correctly:

#### System tools and packages

* cmake for generating autotools build scripts
* autotools (autoconf, automake etc.)
* gcc (other compilers may work but haven't been tested)
* python >= 3.10 (earlier 3.x versions of python may work but haven't been tested)

#### Python packages
* [FMPy >= 0.3.15 in order to generate python-based FMUs](https://github.com/CATIA-Systems/FMPy)
* [pythonfmu >= 0.6.2 in order to generate C FMUs for the python-based simulators (Pandapower etc.)](https://github.com/NTNU-IHB/PythonFMU)
* [Mosaik 3 as a cosimulation master](https://mosaik.offis.de)
* [Pandas is currently used by the collector class for data storage and serialisation.](https://pandas.pydata.org)
* [Matplotlib for visualisation (currently disabled, but the dependency remains for later use.](https://matplotlib.org)
* [Numpy is used by the electrical network calculation.](https://numpy.org)
* [Pandapower provides the electrical loadflow.](http://www.pandapower.org)

#### Build process

The C FMUs (communication simulator) are built using
```bash
foo@bar:~$ ./build_c_fmus.sh
```

The Python FMUs (loadflow and controller) are built using
```bash
foo@bar:~$ ./build_python_fmus.sh
```

## Usage

The demonstration scenario can be started using
```bash
foo@bar:~$ ./run_test_scenario.sh
```
