#ISB-CGC Grid Engine Examples

##Setup Instructions

###Step 0: Read the ISB-CGC Introduction to GCE Documentation

As part of the ISB-CGC documentation on [readthedocs](http://isb-cancer-genomics-cloud.readthedocs.org/en/latest/index.html) 
we have an [introduction](http://isb-cancer-genomics-cloud.readthedocs.org/en/latest/sections/gcp-info/GCE-101.html) to Google Compute Engine (GCE) which you may find useful if you are fairly new to this, including many links to more detailed Google documentation.

###Step 1: Install and Configure Elasticluster on a Compute Engine VM

As described in the above-mentioned introduction on readthedocs, we will use the **gcloud** tool to launch a VM.  You can do this either from the Cloud Shell or from your local workstation where you have installed the Google Cloud SDK.  Using the "startup" script provided (which uses apt-get and pip to install certain packages that will be needed), you can set up a VM to run the Grid Engine example using the following command:
```
gcloud compute instances create grid-engine-workstation \
    --metadata startup-script-url=https://raw.githubusercontent.com/isb-cgc/examples-Compute/master/grid-engine/workstation-startup.sh \
    --scopes https://www.googleapis.com/auth/compute,https://www.googleapis.com/auth/devstorage.full_control
```
If you have not specified your default compute zone, you will be prompted to choose one -- if this occurs, we sugget you set your default compute zone, *eg*: ``gcloud config set compute/zone us-central1-a``.  

If all goes well, in a minute or less you should get a confirmation that looks like this:
```
Created [https://www.googleapis.com/compute/v1/projects/<your-project>/zones/<your-zone>/instances/grid-engine-workstation].
NAME                    ZONE          MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP     STATUS
grid-engine-workstation <your-zone>   n1-standard-1             10.128.0.3  130.211.180.137 RUNNING
```

Once the instance has started, you can ssh to it using the ``gcloud compute ssh`` command:
```
gcloud compute ssh grid-engine-workstation
```
You may again be prompted to specify the zone if you have not set it as part of your configuration.  You may also be warned that an SSH key needs to be generated.  If so, enter "Y" (or press return) to continue.  (You may then also be prompted to enter a passphrase if you want, though you can leave that blank and press return again.  If you do choose to enter a passphrase, make sure you will be able to remember it!  For additional details on connecting to an instance, see [this page](https://cloud.google.com/compute/docs/instances/connecting-to-instance).)

Once logged in, you can finish the setup process by authenticating to Google, using either the ``gcloud init`` or the ``gcloud auth login`` flows.  (This step is necessary because ``gcloud compute ssh`` will have signed you in using project-level service account credentials rather than your personal credentials, and access to data hosted by the ISB-CGC is granted based on user credentials rather than service accounts.  If you run ``gcloud config list`` as soon as you ssh to the instance, you will see that your "account" name is something like ``1087559035271-compute@developer.gserviceaccount.com``.  After you have completed the auth flow, your "account" will be your personal google identity.)

Once you have gone through the auth flow, the next step is to clone this repo and run an additional setup script:
```
git clone https://github.com/isb-cgc/examples-Compute.git
cd examples-Compute/grid-engine
chmod u+x workstation-setup.sh
./workstation-setup.sh
```
These commands will install all of the necessary dependencies and github repos, and partially configure Elasticluster.  Be sure to read the [documentation](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create) for the ``gcloud compute instances create`` command to determine whether you may need additional command line flags to configure your workstation.  Alternatively, you can create an instance under ["Products and Services" -> "Compute Engine"](https://console.cloud.google.com/compute) in the Google Cloud Console.

An SSH keypair for accessing GCE will have also been created by the setup script.  By default, these keys are stored in ~/.ssh/google_compute_engine and ~/.ssh/google_compute_engine.pub.  (For reference, please see this [documentation](http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/index.html#index-generating-ssh-keypair).) 

Next, you will need to customize the required configuration file under ``~/.elasticluster/config.d/``.  For this particular SAMtools example, the file is called ``samtools-index.conf`` and there are four specific places where you need to replace text such as <PROJECT ID> with your own information.  The relevant portion of the config file looks like this:
```
...
[cloud/google-cloud]
provider=google
gce_project_id=<PROJECT ID> 
gce_client_id=<CLIENT ID>
gce_client_secret=<CLIENT SECRET>
...
[login/google-login]
image_user=<GOOGLE ACCOUNT USER NAME>
...
```

  * **gce_project_id** is the name of your Google Cloud Project -- you can find this by running ``gcloud config list``;

  *  **gce_client_id** and **gce_client_secret** refer to an existing OAuth2 client identity in your Google Cloud Project.  If you have not already done so, you can create a new OAuth2 client identity through the Google Cloud Console.  To do this, navigate to  ["Products and Services" -> "API Manager" -> "Credentials"](https://console.cloud.google.com/apis/credentials) in the Cloud Console.  Click on "Create Credentials" -> "OAuth client id", then choose "Other", give it a name such as "Elasticluster1" and click "Create". A pop-up will show you your new client ID and client secret, which you can cut and paste into the configuration file. (For more details, refer to this [documentation](http://googlegenomics.readthedocs.org/en/latest/use_cases/setup_gridengine_cluster_on_compute_engine/index.html#index-obtaining-client-id-and-client-secrets).

  * **image_user** will be your username on the Grid Engine cluster -- you can find this by running ``whoami``.

You may refer to the [Elasticluster configuration documentation](http://elasticluster.readthedocs.org/en/latest/configure.html) for more information about each required configuration parameter.

This configuration file defines a cluster named "samtools-index" with one master node and 5 compute nodes.

###Step 2: Create the Grid Engine Cluster

To create a Grid Engine cluster, first activate the Python virtual environment created for you by the workstation setup script:
```
source ~/virtualenv/elasticluster/bin/activate
```

Then run the following command to start the cluster setup process:
```
elasticluster start <cluster-name>
```

The "cluster-name" was defined in the configuration file, and for this example is "samtools-index".  (The cluster names can be found in the "cluster" sections of a configuration file.  For example, the "samtools-index" cluster name can be found on the line "[cluster/samtools-index]" in [examples-Compute/grid-engine/elasticluster/config.d/samtools-index.conf](./elasticluster/config.d/samtools-index.conf).)

Note that projects have quota limits to protect you from accidentally spinning up thousands of VMs at once.  If your quota is insufficient to run this example, you may see the following type of error: 
```
grid-engine-workstation gc3.elasticluster[10019] ERROR Error creating instance The following error occurred while interactin
g with the cloud provider Quota 'CPUS' exceeded.  Limit: 8.0
```

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

For more information about each of the required options for the script, run "python index_bam_files.py -h".  Additional information about the script can also be found on the script's [README](./samtools-index/README.md) page.

###Step 6: Clean up

To delete your grid engine cluster once you're finished with it, run the following Elasticluster command:
```
elasticluster stop <cluster-name>
```
