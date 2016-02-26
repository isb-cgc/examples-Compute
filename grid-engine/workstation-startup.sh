#!/bin/bash
# install dependencies
apt-get -qq update
apt-get -qq install git build-essential python-dev libffi-dev python-software-properties
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
pip install virtualenv
gcloud -q components update