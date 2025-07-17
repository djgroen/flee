## **Dependencies**

To use the Flee code, you need:

* Python 3 interpreter (3.7 or higher)
* Python libraries:
	- numpy ([https://www.numpy.org](https://www.numpy.org))
	- pandas ([https://pandas.pydata.org](https://pandas.pydata.org))
	- matplotlib ([https://matplotlib.org](https://matplotlib.org))
	- scipy ([https://scipy.org](https://scipy.org))
	- folium ([https://python-visualization.github.io/folium/](https://python-visualization.github.io/folium/))
	- ipython ([https://ipython.org](https://ipython.org))
* [git](https://git-scm.com/docs/git) needs to be installed on your machine.
* [mpirun](https://www.open-mpi.org/) needs to be installed on your machine.

## **Installing Flee**

To install Flee on your local workstation, follow these steps:

1. Clone the Flee repository:
	```sh
	git clone https://github.com/djgroen/flee.git
	```
	Once cloning completes, Flee will appear in your working directory as `<current dir>/flee`.

2. (Recommended) Create and activate a Python virtual environment:
	```sh
	cd flee
	python3 -m venv venv
	source venv/bin/activate
	```
	> **Note:** On Windows, activate the environment with `venv\Scripts\activate`.

3. Install the required Python libraries:
	```sh
	pip install -r requirements.txt
	```

4. Open the appropriate shell configuration file:
	- For Linux users and Mac users with a bash shell (default for many Linux distributions):
	```sh
	vim ~/.bashrc
	```
	- For Mac users using zsh (the default shell on macOS Catalina and later):
	```sh
	vim ~/.zshrc
	```

5. Add the following line to the end of the file:
	```sh
	export PYTHONPATH=<path to flee>:$PYTHONPATH
	```
6. Save and close the file, then reload the configuration:
	- For bash:
	```sh
	source ~/.bashrc
	```
	- For zsh:
	```sh
	source ~/.zshrc
	```

> **Note:** On some systems, you may need to use `pip3` instead of `pip`, and `python3` instead of `python`, depending on how Python is installed. Adjust the commands accordingly if you encounter issues.

## **Updating Flee**

If you have already installed Flee and want to update to the latest version, in your local Flee directory simply type

```sh
git pull
```

## **Testing Flee**

To run the basic tests, simply type

```sh
cd flee
pytest tests/
```

> **Note:** If all the tests are failing, please review the installation instructions above and ensure you have installed all required libraries using `requirements.txt`. If you are unable to resolve the issues, consider opening a GitHub issue or getting in touch for further assistance.

If you have FabFlee installed, then you can also run the FabFlee tests. To prepare for this, go to your main Flee directory and create a symbolic link using:

```sh
ln -s <main FabFlee directory> FabFlee
```

After that, you can then perform the tests using `pytest tests_mpi`.

Lastly, to do a simple single test run, use `python3 tests/test_csv.py`.
