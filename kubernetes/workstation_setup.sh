#!/bin/bash

sudo apt-get -qq update
sudo apt-get -qq install python-dev python-software-properties libffi-dev git
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
sudo pip install virtualenv
sudo gcloud components install kubectl
#sudo gcloud components install beta
sudo gcloud components update
if [[ ! -d $HOME/virtualenv ]]; then mkdir -p $HOME/virtualenv; fi
virtualenv $HOME/virtualenv/toil
source $HOME/virtualenv/toil/bin/activate
pip install toil requests json-spec httplib2 google-api-python-client


