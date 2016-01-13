#!/bin/bash

cd $1 # install dir given as first positional param
# install dependencies
sudo apt-get -qq update
sudo apt-get -qq install git python-dev libffi-dev
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
sudo pip install virtualenv
sudo gcloud -q components update
# set up a virtualenv for elasticluster
mkdir virtualenv
cd virtualenv
virtualenv elasticluster
source elasticluster/bin/activate 
pip install --upgrade google-api-python-client
# install elasticluster
cd elasticluster
git clone https://github.com/gc3-uzh-ch/elasticluster.git src
cd src && python setup.py install && cd ..
# set up elasticluster configuration
git clone https://github.com/isb-cgc/examples-Compute.git
mkdir ~/.elasticluster && touch ~/.elasticluster/config
cp -R examples-Compute/grid-engine/elasticluster/config.d ~/.elasticluster

export ISB_ACCESS_SCRIPTS_DIR=$PWD/ISB-CGC-Webapp/scripts
export GRID_COMPUTING_TOOLS_DIR=$PWD/grid-computing-tools
export PYTHONPATH=$PYTHONPATH:$ISB_ACCESS_SCRIPTS_DIR


