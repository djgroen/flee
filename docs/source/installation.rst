.. _installation:

Installation and Testing
========================

Dependencies
------------

To use the Flee code, one requires:

- Python 3 interpreter
- Python libraries

   - numpy (see https://www.numpy.org)
   - pandas (see https://pandas.pydata.org)
   - matplotlib (see https://matplotlib.org)
   - scipy (see https://scipy.org)

* **git** needs to be installed in your machine. 

Installing Flee
---------------
 
To install Flee on your local workstation, you need to clone the Flee repository:


    .. code:: console

            git clone https://github.com/djgroen/flee.git
        
        
        
Once cloning completes, Flee will appear in your working directory as ``~/flee``.


Updating Flee
-------------

If you have already installed Flee and want to update to the latest version, in your local Flee directory simply type 

    .. code:: console
    
            git pull
            
            
            
Testing Flee
------------

To run the test example, simply type

    .. code:: console
    
            cd flee
            python3 test-csv.py
          

    .. note :: test-csv is an example scenario for testing purposes. 

