#!/bin/bash

echo "export PATH=$PATH:/usr/local/share/google/google-cloud-sdk/bin" >> ~/.bashrc
if [[ ! -d $HOME/virtualenv ]]; then mkdir -p $HOME/virtualenv; fi
virtualenv $HOME/virtualenv/toil
source $HOME/virtualenv/toil/bin/activate
pip install toil requests json-spec httplib2 google-api-python-client


