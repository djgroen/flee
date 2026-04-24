# Installation

This page explains how to install Flee on your local machine.

## Dependencies

Flee requires the following:

- Python 3.7 or higher
- Python packages: `numpy`, `pandas`, `matplotlib`, `scipy`, `folium`, `ipython`
- [git](https://git-scm.com/) — for cloning the repository and updating
- [mpirun](https://www.open-mpi.org/) — only required if you want to run parallel simulations with pflee

## Step-by-step installation

### 1. Clone the repository

```sh
git clone https://github.com/djgroen/flee.git
```

This will create a `flee/` directory in your current working directory.

### 2. Create a virtual environment (recommended)

Using a virtual environment keeps Flee's dependencies isolated from your system Python installation.

```sh
cd flee
python3 -m venv venv
source venv/bin/activate
```

!!! note
    On Windows (if using WSL, skip this note), activate the environment with `venv\Scripts\activate`.

### 3. Install Python dependencies

```sh
pip install -r requirements.txt
```

!!! tip
    On some systems you may need to use `pip3` and `python3` instead of `pip` and `python`.

### 4. Add Flee to your Python path

Open your shell configuration file:

=== "Linux (bash)"
    ```sh
    vim ~/.bashrc
    ```

=== "macOS (zsh)"
    ```sh
    vim ~/.zshrc
    ```

Add the following line at the end of the file, replacing `<path to flee>` with the absolute path to your cloned `flee/` directory:

```sh
export PYTHONPATH=<path to flee>:$PYTHONPATH
```

Save the file and reload your shell:

=== "Linux (bash)"
    ```sh
    source ~/.bashrc
    ```

=== "macOS (zsh)"
    ```sh
    source ~/.zshrc
    ```

## Updating Flee

If you have already installed Flee and want to update to the latest version, run the following inside your Flee directory:

```sh
git pull
pip install -r requirements.txt
```

## Next steps

- [Run your first simulation](quick-start.md)
- [Run the test suite](testing.md) to verify everything works
