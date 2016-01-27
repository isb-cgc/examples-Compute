#!/bin/bash

# install dependencies
sudo apt-get -qq update
sudo apt-get -qq install git python-dev libffi-dev
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
sudo pip install virtualenv
if [[ ! -d ~/virtualenv ]]; then
	mkdir ~/virtualenv
fi
cd ~/virtualenv
virtualenv isb_cgc_venv
source isb_cgc_venv/bin/activate
pip install pyopenssl ndg-httpsclient pyasn1 requests
pip install --upgrade google-api-python-client

# install required code repos
cd ~/
git clone https://github.com/isb-cgc/examples-Compute.git
git clone https://github.com/isb-cgc/ISB-CGC-Webapp.git
git clone https://github.com/googlegenomics/grid-computing-tools.git

