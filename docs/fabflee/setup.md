# FabFlee — installation and setup

This page covers installing all components needed to use FabFlee.

---

## Prerequisites

- macOS or Linux (Windows via WSL)
- Python 3.8+
- Git

---

## Step 1 — Install Flee

If you haven't already installed Flee, follow the [Flee installation guide](../getting-started/installation.md).

We will assume Flee is installed at `~/flee/`.

---

## Step 2 — Install Flare (optional)

Flare is a stochastic conflict evolution model used for ensemble conflict scenario runs. It is optional unless you want to run coupled Flare+Flee simulations.

```sh
git clone https://github.com/djgroen/flare-release.git ~/flare-release
```

---

## Step 3 — Install FabSim3

Full FabSim3 installation instructions are at [fabsim3.readthedocs.io](https://fabsim3.readthedocs.io/en/latest/installation.html).

Quick install:

```sh
git clone https://github.com/djgroen/FabSim3.git ~/FabSim3
cd ~/FabSim3
pip install -r requirements.txt
```

Then configure your paths in `~/FabSim3/fabsim/deploy/machines_user.yml`.

---

## Step 4 — Install the FabFlee plugin

From the FabSim3 directory:

```sh
fabsim localhost install_plugin:FabFlee
```

The plugin will be installed to `~/FabSim3/plugins/FabFlee/`.

---

## Step 5 — Configure machines_user.yml

Open `~/FabSim3/fabsim/deploy/machines_user.yml` and add the following under the `default:` section:

```yaml
default:
  flee_location: /path/to/flee
  flare_location: /path/to/flare-release   # only if Flare is installed
```

Replace the paths with your actual installation directories.

Also configure `machines_FabFlee_user.yml` in the FabFlee plugin directory:

1. Go to `~/FabSim3/plugins/FabFlee`
2. Duplicate `machines_FabFlee_user_example.yml` and name the copy `machines_FabFlee_user.yml`
3. Open `machines_FabFlee_user.yml` and add under `localhost:`:

```yaml
localhost:
  flee_location: /path/to/flee
```

---

## Step 6 — Verify the installation

Run a quick test to confirm everything is working:

```sh
fabsim localhost sflee:mali2012,simulation_period=10
fabsim localhost fetch_results
```

If this completes without errors, FabFlee is working correctly.

---

## Upgrading FabFlee

To update to the latest version of the FabFlee plugin:

1. Go to `~/FabSim3/plugins/FabFlee`
2. Run `git pull`
3. Wipe any `config_files` directories on remote machines to avoid conflicts with leftover files from older versions

---

## Troubleshooting

**`fabsim` not found**: Ensure `~/FabSim3/` is in your `PATH`, or use the full path: `~/FabSim3/fabsim/bin/fabsim`.

**Import errors**: Ensure `PYTHONPATH` includes your Flee directory:
```sh
export PYTHONPATH=$PYTHONPATH:~/flee
```

**SSH errors on localhost**: FabSim3 uses SSH internally for remote execution. Ensure passwordless SSH to localhost is configured:
```sh
ssh-copy-id localhost
```

---

## Next steps

- [Running locally with FabFlee](running-local.md) — how to run Flee via FabFlee
- [Running on HPC](hpc.md) — configuring a remote machine
