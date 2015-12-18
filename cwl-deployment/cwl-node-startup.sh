#!/bin/bash

# Install pip
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py && rm get-pip.py

# Install CWL reference implementation
pip install cwl-runner

# Create the data directory used by the example
mkdir -p /cwl-data/workflows/inputs 

