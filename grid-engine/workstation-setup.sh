#!/bin/bash

# install dependencies
sudo apt-get -qq update
sudo apt-get -qq install git python-dev libffi-dev
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
sudo pip install virtualenv
sudo gcloud -q components update
# set up a virtualenv for elasticluster
if [[ ! -d ~/virtualenv ]]; then
	mkdir ~/virtualenv
fi
cd ~/virtualenv
virtualenv elasticluster
source elasticluster/bin/activate 
pip install --upgrade google-api-python-client
# install elasticluster
cd elasticluster
git clone https://github.com/gc3-uzh-ch/elasticluster.git src
cd src && python setup.py install && cd ..
# set up elasticluster configuration
if [[ ! -d ~/.elasticluster ]]; then
	mkdir ~/.elasticluster && touch ~/.elasticluster/config
fi
cp -R elasticluster/config.d ~/.elasticluster



