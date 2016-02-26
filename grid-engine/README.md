#ISB-CGC Grid Engine Examples

##Setup Instructions

###Step 0: Read the ISB-CGC Compute Documentation

A link is coming soon... please check back again later.

###Step 1: Install and Configure Elasticluster on a Compute Engine VM

The easiest way to set up a VM to run the Grid Engine examples is to run some variation of the following command:
```
gcloud compute instances create grid-engine-workstation --metadata startup-script-url=https://raw.githubusercontent.com/isb-cgc/examples-Compute/master/grid-engine/workstation-startup.sh
```

Once the instance has started, you can ssh to it using the `gcloud compute ssh` command:
```
gcloud compute ssh grid-engine-workstation
```

Once logged in, you can finish the setup process by authenticating to Google, cloning this repo and running an additional setup script:
```
gcloud auth login  # use the same identity that you used to create the instance
git clone https://github.com/isb-cgc/examples-Compute.git
cd examples-Compute/grid-engine
chmod u+x workstation-setup.sh
./workstation-setup.sh
```

The above command will install all of the necessary dependencies and github repos, and partially configure Elasticluster.  Be sure to read the [documentation](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create) for the `gcloud compute instances create` command to figure out what additional command line flags you will need to configure your workstation.  Alternatively, you can create an instance under ["Products and Services" -> "Compute Engine"](https://console.cloud.google.com/compute) in the Google Developer's Console.

You will also need to provide some additional configuration values for each configuration file created by the workstation setup script in ~/.elasticluster/config.d.  The required manual configuration can be found in the individual files with in ~/.elasticluster/config.d, as follows:

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

"gce_project_id" will be the name of the Google Cloud Project that you want to create your instance in.  This is usually a string of all lowercase letters, numbers, and dashes.

"gce_client_id" and "gce_client_secret" refer to an existing Oauth2 client identity in your Google Cloud Project.  If you haven't already, you can create a new Oauth2 client identity through the Google Developer's Console.  To do this, navigate to  ["Products and Services" -> "API Manager" -> "Credentials"](https://console.cloud.google.com/apis/credentials) in the Developer's Console.  Once the API Manager screen loads, click "New Credentials" -> "Oauth2 client id", and then follow all the prompts.  For more information about how to find your client id and client secret, see the documentation [here](http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/index.html#index-obtaining-client-id-and-client-secrets).

"image_user" will be the Linux username created for you on the Grid Engine cluster.

You will also need to make sure that you have generated an SSH keypair for accessing GCE.  By default, these keys are stored in ~/.ssh/google_compute_engine and ~/.ssh/google_compute_engine.pub.  This step is already done for you in the workstation setup script.  For reference, see the documentation [here](http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/index.html#index-generating-ssh-keypair). 

Refer to the [Elasticluster configuration documentation](http://elasticluster.readthedocs.org/en/latest/configure.html) for more information about each required configuration parameter.

###Step 2: Create the Grid Engine Cluster

To create a Grid Engine cluster, first activate the Python virtual environment created for you by the workstation setup script:
```
source ~/virtualenv/elasticluster/bin/activate
```

Then run the following command to start the cluster setup process:
```
elasticluster start <cluster-name>
```

The "cluster-name" should match the name of a particular cluster in one of the configuration files.  The cluster names can be found in the "cluster" sections of each configuration file.  For example, the "samtools-index" cluster name can be found on the line "[cluster/samtools-index]" in [examples-Compute/grid-engine/elasticluster/config.d/samtools-index.conf](./elasticluster/config.d/samtools-index.conf).

###Step 3: Copy the grid engine master setup script to the Grid Engine master 

Once the setup has run successfully to completion, copy the setup script to the Grid Engine master node:
```
elasticluster sftp <cluster-name> << 'EOF'
put examples-Compute/grid-engine/grid-engine-master-setup.sh
EOF
```

###Step 4: Log into the Grid Engine master and run the setup script

Run the following command to ssh to the master node of your Grid Engine cluster:
```
elasticluster ssh <cluster-name>
```

Then run the setup script that you just copied to the master:
```
chmod u+x grid-engine-master-setup.sh
./grid-engine-master-setup.sh
```
###Step 5: Run the examples

You should now be ready to run the example scripts on your Grid Engine cluster.  For example, to run the "samtools-index" operation, run the following commands:
```
gcloud auth login
source ~/virtualenv/isb_cgc_venv/bin/activate
cd ~/examples-Compute/grid-engine/samtools-index
PYTHONPATH=$PYTHONPATH:~/ISB-CGC-Webapp/scripts python index_bam_files.py [OPTIONS]
```

For more information about each of the required options for the script, run "python index_bam_files.py -h".

###Step 6: Clean up

To delete your grid engine cluster once you're finished with it, run the following Elasticluster command:
```
elasticluster stop <cluster-name>
```
