#!/bin/bash

sudo apt-get -qq update
sudo apt-get -qq install git python-dev libffi-dev
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
sudo pip install pyopenssl ndg-httpsclient pyasn1 requests
sudo pip install --upgrade google-api-python-client
git clone https://github.com/isb-cgc/examples-Compute.git
git clone https://github.com/isb-cgc/ISB-CGC-Webapp.git
git clone https://github.com/googlegenomics/grid-computing-tools.git
sudo gcloud -q components update

export ISB_ACCESS_SCRIPTS_DIR=$PWD/ISB-CGC-Webapp/scripts
export GRID_COMPUTING_TOOLS_DIR=$PWD/grid-computing-tools
export PYTHONPATH=$PYTHONPATH:$ISB_ACCESS_SCRIPTS_DIR


