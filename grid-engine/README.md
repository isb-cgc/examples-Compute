#ISB-CGC Grid Engine Examples

##Setup Instructions

###Step 1: Install and Configure Elasticluster

Follow the steps for installing Elasticluster in the [Elasticluster installation documentation](http://elasticluster.readthedocs.org/en/latest/install.html).  Then, set up the Elasticluster configuration directory with the following commands:
```
cd ~
git clone https://github.com/isb-cgc/examples-Compute.git
mkdir -p .elasticluster/config.d
touch .elasticluster/config
cp examples-Compute/grid-engine/elasticluster/config.d/* ./.elasticluster/config.d
```

Alternatively, you can just run the script "workstation-setup.sh" in this directory, which will install elasticluster for you in a virtualenv, along with all of its dependencies.

You will also need to provide some additional configuration values for each configuration file in ./elasticluster/config.d.  The required manual configuration can be found in the individual files with in ~/.elasticluster/config.d, as follows:

```
...
[cloud/google-cloud]
...
gce_project_id=<YOUR GOOGLE PROJECT ID HERE> 
gce_client_id=<YOUR GOOGLE CLIENT ID HERE>
gce_client_secret=<YOUR GOOGLE CLIENT SECRET HERE>
...
[login/google-login]
image_user=<YOUR LOGIN USER NAME HERE>
image_user_sudo=root
image_sudo=True
user_key_name=elasticluster
user_key_private=~/.ssh/google_compute_engine # be sure to check that these exist
user_key_public=~/.ssh/google_compute_engine.pub
...
```

"image_user" will be the Linux username created for you on the Grid Engine cluster.

You can find your GCE project id, client id, and client secret by logging into the Google Developer's Console (console.developers.google.com).  Your project id can be seen in the top-right corner of the Developer's Console.  For more information about how to find your client id and client secret, see the documentation [here](http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/index.html#index-obtaining-client-id-and-client-secrets).

You will also need to make sure that you have generated an SSH keypair for accessing GCE.  By default, these keys are stored in ~/.ssh/google_compute_engine and ~/.ssh/google_compute_engine.pub.  For more information about how to generate the SSH keypair, see the documentation [here](http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/index.html#index-generating-ssh-keypair). 

Refer to the [Elasticluster configuration documentation](http://elasticluster.readthedocs.org/en/latest/configure.html) for more information about each required configuration parameter.

###Step 2: Create the Grid Engine Cluster

To create a Grid Engine cluster, run the following command:
```
elasticluster start <cluster-name>
```

The "cluster-name" should match the name of a particular cluster in one of the configuration files.  The cluster names can be found in the "cluster" sections of each configuration file.  For example, the "samtools-index" cluster name can be found on the line "[cluster/samtools-index]" in [examples-Compute/grid-engine/elasticluster/config.d/samtools-index.config](elasticluster/config.d/samtools-index.config).

###Step 3: Copy the setup script to the Grid Engine master 

Once the setup has run successfully to completion, copy the setup script to the Grid Engine master node:
```
elasticluster sftp <cluster-name> << 'EOF'
put examples-Compute/grid-engine/isb-cgc-setup.sh
EOF
```

###Step 4: Log into the Grid Engine master and run the setup script

Run the following command to ssh to the master node of your Grid Engine cluster:
```
elasticluster ssh <cluster-name>
```

Then run the setup script that you just copied to the master:
```
./isb-cgc-setup.sh
```
###Step 5: Run the examples

You should now be ready to run the example scripts on your Grid Engine cluster.  For example, to run the "samtools-index" operation, run the following commands:
```
cd examples-Compute/grid-engine/samtools-index
python index_bam_files.py [OPTIONS]
```

For more information about each of the required options for the script, run "python index_bam_files.py -h".
