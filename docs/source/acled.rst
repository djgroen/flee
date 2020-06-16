.. _acled:

Automation for creating a locations.csv from ACLED database
===========================================================

This tutorial focuses on automated extraction of a `locations.csv` input file from the Armed Conflict Location and Event Data Project [(ACLED)](https://acleddata.com), which provides conflict location data for forced displacement simulations. The `locations.csv` has the following format:

+------+--------+---------+-----+------+---------------+---------------+---------------------+
| name | region | country | lat | long | location_type | conflict_date | population/capacity |
+======+========+=========+=====+======+===============+===============+=====================+
| A    |   AA   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
+------+--------+---------+-----+------+---------------+---------------+---------------------+
| B    |   BB   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
+------+--------+---------+-----+------+---------------+---------------+---------------------+
| C    |   CC   |   ABC   | xxx |  xxx |    conflict   |      xxx      |         xxx         |
+------+--------+---------+-----+------+---------------+---------------+---------------------+


The procedure of an automated extraction 
----------------------------------------

1. Getting conflict data from ACLED database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To obtain data on a chosen conflict situation, complete the ACLED data export tool fields (https://acleddata.com/acleddatanew/data-export-tool/) as follows:

- Provide dates of interest for conflict situation (i.e. From and To).
- Select Event Type: Battles.
- Select Sub Event Type: Armed clash, Attack, Government regains territory and Non-state actor overtakes territory.
- Specify Region and Country of conflict situation choice.
- Click on Export and Accept Terms of Use and Attribution Policy.
- Click Export again and <name>.csv file exports to Downloads automatically.

There are two options at this point:

- Rename the file <name>.csv to `acled.csv` and place it in the relevant conflict directory in `config_files`. For example, if you collected data for Mali, you would place it in `(FabSim3 Home)/plugins/FabFlee/config_files/mali`;

- Keep it as it is, and use the ``path=`` argument when issuing the process_acled command.


2. Constructing a locations.csv input file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To construct conflict locations input file from ACLED for the FabFlee simulations, simply type:

.. code:: console

          fabsim localhost process_acled:country=<country>,start_date=<dd-mm-yyyy>,filter=earliest/fatalities

If your <name>.csv file is not stored in a conflict directory of `config_files`:

.. code:: console

          fabsim localhost process_acled:country=<country>,start_date=<dd-mm-yyyy>,filter=earliest/fatalities,path=<~/path/to/<name>.csv>

.. note:: 

- **country** is the name of the country directory the acled.csv is stored in.
- **start_date** uses dd--mm-yyyy format and is the date which conflict_date will be calculated from.
- **filter** takes earliest or fatalities. Earliest will keep the first occurring (using date) location and remove all occurrences that location after that date. Fatalities will keep the highest fatalities of each location and remove all other occurrences of that location.
- **path** is the path to your acled csv file if it is not already stored in config_files. This argument is optional.

This will produce the locations.csv into the input_csv directory in `(FabSim3 Home)/plugins/FabFlee/config_files/<conflict_name>` for the given country. If there is not an `input_csv` folder in the conflict situation directory, one will be created.


To demonstrate, the following command uses the Mali conflict situation:  

.. code:: console

          fabsim localhost process_acled:country=mali,start_date=20-01-2010,filter=earliest    

In this case, the locations.csv can be found in `(FabSim3 Home)/plugins/FabFlee/config_files/mali/input_csv`. 


Currently, the population figures for each location will need to be collected and written to the `population/capacity` column manually using a resource, such as www.citypopulation.de. After the population data has been collected for each location, input these population numbers in `locations.csv`, which can be then used for simulation execution.
