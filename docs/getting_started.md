# Getting Started

1. Start by cloning this repo to your environment and changing directory into it:
  * `git clone https://github.com/dlotterman/metal_ra.git`
  * `cd metal_ra`
2. Export environment variables, this assumes a config file from [metal-cli](https://github.com/equinix/metal-cli)
  * `export METAL_ORG_ID=$(cat ~/.config/equinix/metal.yaml  | grep "organization-id:" | awk '{print$NF}')`
  * `export METAL_AUTH_TOKEN=$(cat ~/.config/equinix/metal.yaml  | grep "token:" | awk '{print$NF}')`

Your next steps depend on your prefered path:
1. Python
  i. Requires modern-ish `python`, say `python3.3`?
	* Any modern Ubuntu or Enterprise Linux should be fine, OSX `python3.12` should work fine if you setup pip / homebrew.
2. Docker / Podman
  ii. Assumes pre-installation

### Python

* `python -m venv .venv`
* `pip install -r requirements.txt`
* `source .venv/bin/activate`
* `python metal_ra.py`

### Docker / Podman

This guide assumes [podman](https://podman.io/), the native container runtime in Enterprise Linux. `docker` should work as expected, string of `podman` for `docker` in the commands.

* `mkdir /tmp/results`
* `podman build . -t metal_ra`
* `podman run -v /tmp/results/:/tmp/ -e METAL_ORG_ID -e METAL_AUTH_TOKEN metal_ra:latest`
