#!/bin/bash

# Install pip
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py && rm get-pip.py

# Install CWL reference implementation
pip install cwl-runner

# Add the docker group to avoid requiring sudo
# https://docs.docker.com/engine/installation/debian/#giving-non-root-access
groupadd docker

# Clone the git repo under /git_home/isb-cgc
mkdir -p /git_home/isb-cgc
cd /git_home/isb-cgc
git clone https://github.com/isb-cgc/examples-Compute.git
chgrp -R docker /git_home
chmod -R g+w /git_home

# Create the /cwl-data directory used by the CWL examples
mkdir -p /cwl-data/workflows/inputs 
chgrp -R docker /cwl-data
chmod -R g+w /cwl-data
