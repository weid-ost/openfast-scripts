==================================
Python Package pyOF
==================================

Repository for OpenFAST scripts, including

- input file manipulation
- run scripts
- post-processing and plotting


Installation
--------------------
.. hint::
    To avoid collisions with your system's library versions,
    use a python virtual environment for installation. See
    `Virtual environments`_ below.

You can install the latest version of the library from its repository

::

    pip install "git+https://github.com/weid-ost/openfast-scripts.git"

Usage
-------

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
