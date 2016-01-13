#!/bin/bash

cd $1 # install dir given as first positional param
# install dependencies
sudo apt-get -qq update
sudo apt-get -qq install git python-dev libffi-dev
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
sudo pip install virtualenv
sudo gcloud -q components update
# set up a virtualenv for the examples
mkdir virtualenv
cd virtualenv
virtualenv isb_compute_examples
source isb_compute_examples/bin/activate
pip install pyopenssl ndg-httpsclient pyasn1 requests 
pip install --upgrade google-api-python-client
# install elasticluster
cd isb_compute_examples
git clone https://github.com/gc3-uzh-ch/elasticluster.git 
cd elasticluster && python setup.py install && cd ..
# install isb code repos
git clone https://github.com/isb-cgc/ISB-CGC-Webapp.git
git clone https://github.com/googlegenomics/grid-computing-tools.git
# set up elasticluster configuration
mkdir ~/.elasticluster && touch ~/.elasticluster/config
cp -R examples-Compute/grid-engine/elasticluster/config.d ~/.elasticluster

export ISB_ACCESS_SCRIPTS_DIR=$PWD/ISB-CGC-Webapp/scripts
export GRID_COMPUTING_TOOLS_DIR=$PWD/grid-computing-tools
export PYTHONPATH=$PYTHONPATH:$ISB_ACCESS_SCRIPTS_DIR


