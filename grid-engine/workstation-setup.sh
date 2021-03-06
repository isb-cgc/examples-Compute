#!/bin/bash

this_dir=$PWD
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
cd $this_dir

cp -R elasticluster/config.d ~/.elasticluster
if [[ ! -a ~/.ssh/google_compute_engine || ! -a ~/.ssh/google_compute_engine.pub ]]; then
	gcloud compute config-ssh
fi



