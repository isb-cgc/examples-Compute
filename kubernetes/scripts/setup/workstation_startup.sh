#!/bin/bash

apt-get -qq update
apt-get -qq install python-dev python-software-properties libffi-dev git
wget https://bootstrap.pypa.io/get-pip.py && sudo python get-pip.py && rm get-pip.py
pip install virtualenv
gcloud components update
gcloud components install kubectl
