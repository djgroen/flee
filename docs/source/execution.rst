.. _execution:

.. Simulation instance execution
.. =============================

Execute test instance
=======================

To run simulation instance using Flee with test, simply type::

  python3 run_csv_vanilla.py test_data/test_input_csv test_data/test_input_csv/refugee_data 5 2010-01-01 2>/dev/null
  
  .. note:: The "2>/dev/null" ensures that any diagnostics are not displayed on the screen. Instead, pure CSV output for the toy model should appear on the screen if this works correctly.
  

Execute a conflict scenario
===========================

1. Create an output directory **out<country_name>**.

2. Run the following command to execute <country_name>.py and obtain the simulation output, which will be written to out<country_name> as out.csv:

   python3 <country_name>.py <simulation_period> > out<country_name>/out.csv

3. Plot the simulation output using:

   python3 plot-flee-output.py out<country_name>

4. To analyse and interpret simulation output, open out<country_name>, which will contain simulation output and UNHCR data comparison graphs for each camp, as well as average relative difference graph for the simulated conflict situation.

   

Execute simplified simulation of Central African Republic (CAR) situation:
=========================================================================

To run the (simplified) CAR simulation:

1. Create an output directory **outcar**.

2. Execute car-csv.py and obtain the simulation output:

   python3 car-csv.py 50 > outcar/out.csv

3. Plot the simulation output using:

   python3 plot-flee-output.py outcar
    
4. Analyse and interpret simulation output graphs in outcar

