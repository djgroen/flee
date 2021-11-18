## **Dependencies**

To use the Flee code, one requires:

* Python 3 interpreter
* Python libraries
	- numpy (see [https://www.numpy.org](https://www.numpy.org))
	- pandas (see [https://pandas.pydata.org](https://pandas.pydata.org))
	- matplotlib (see [https://matplotlib.org](https://matplotlib.org))
	- scipy (see [https://scipy.org](https://scipy.org))
* [git](https://git-scm.com/docs/git) needs to be installed in your machine.


## **Installing Flee**

To install Flee on your local workstation, you need to clone the Flee repository:
```sh
git clone https://github.com/djgroen/flee.git
```
Once cloning completes, Flee will appear in your working directory as `<current dir>/flee`.


## **Updating Flee**

If you have already installed Flee and want to update to the latest version, in your local Flee directory simply type

```sh
git pull
```

## **Testing Flee**

To run the test example, simply type

```sh
cd flee
python3 tests/test_csv.py
```