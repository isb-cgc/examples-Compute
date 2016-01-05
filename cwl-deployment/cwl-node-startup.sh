#!/bin/bash

# Install pip
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py && rm get-pip.py

# Install CWL reference implementation
pip install cwl-runner

# Add the docker group
groupadd docker

# Create the data directory used by the example
mkdir -p /cwl-data/workflows/inputs 
chgrp -R docker /cwl-data
chmod -R g+w /cwl-data
