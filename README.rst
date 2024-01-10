==================================
Python Package pyOF
==================================

Repository for OpenFAST scripts, including

- input file manipulation
- run scripts
- post-processing and plotting


Installation
--------------------
To avoid collisions with your system's library versions,
use a python virtual environment for installation. See
`Virtual Environment Primer`__.

 .. _venv: https://realpython.com/python-virtual-environments-a-primer/

__venv_

The easiest way to use the scripts within this library is to download the whole repository and then execute
::

    pip install -e .

``openfast-scripts`` depends on the package ``openfast_toolbox`` (https://github.com/OpenFAST/openfast_toolbox).
Follow the package installation instructions for further details.

Usage
-------
The library is structured as shown in the following:

.. code-block:: text

   openfast-scripts/
   |--pyOF/
   |  |--case_gen_config.yaml
   |  |--cases.py
   |  |--io.py
   |  |--postpro.py
   |  |--scada.py
   |  |--utils.py
   |  |--wind_input.py
   |--run.sh
   |--run.py

``case_gen_config.yaml`` contains the information about your OpenFAST installation and the case generation and currently needs to be located in the ``pyOF/`` folder.

.. code-block:: yaml

    # YAML file for configuring the case generation
    case:
      name: power_curve
      ref_dir: path/to/ref_folder
      case_dir: path/to/output_dir
      main_file: runAventa.fst
      fast_exe: path/to/bin/openfast
      turbsim_exe: path/to/bin/turbsim
      inputs:
        seed: 20230317
        turbine:
          cut_in: 2.0
          cut_out: 14.0
        wind:
          weibull:
            A: 6.0
            k: 2.0
          turb_int_ref:
            mean: 18.0
            sd: 7.0
          yaw_error:
            mean: 0.0
            sd: 5.0
        n_inputs: 128
  
``ref_dir`` points to the path of your base OpenFAST simulation setup, from which the different cases will be derived and generated.
In the ``case_dir`` folder the generated cases will be written out. 
The main OpenFAST file is defined with ``main_file``.
An example setup is given in the ``tests/`` folder.

The scripts within this library call the OpenFAST executable and the TurbSim executable. In order for the scripts to find those executables, the paths have to be set with the fields ``fast_exe`` and ``turbsim_exe``.

Next, the inputs for the case generation need to be filled out.
The ``seed`` field is used with the random number generator. Setting it to a fixed value, the case generation outputs will stay the same, no matter how often the scripts are run.
With the ``wind`` fields the distributions for the wind speeds, turbulence intensities and yaw errors are given from which samples are drawn for the case generation.
``n_inputs`` is the number of cases to be created and simulated.


In ``pyOF/cases.py`` are the following four functions that should be run in the same order:

1. ``generate_power_curve_case`` -> Case generation
2. ``generate_turb_sim_bts``     -> Case generation
3. ``run_simulations``           -> Simulations (Optional)
4. ``create_10min_ave``          -> Post-processing (Optional)  

After installing this library (``pip install -e .``), these commands should be now available to be run in a terminal, see ``run.sh``.
Alternatively, ``run.py`` can be used. 

