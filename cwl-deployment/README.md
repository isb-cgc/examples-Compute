#ISB-CGC Single-Node Workflow Deployment

This directory contains files that you can use to create a deployment for running CWL workflows on a single Google Compute Engine (GCE) VM (virtual machine).  

##Prerequisites
In order to spin up a GCE VM, you will need access to a Google Cloud project (GCP), and you will also need a local installation of the [Google Cloud SDK](https://cloud.google.com/sdk/).  If you are not yet an ISB-CGC user, please sign-in to the [web-app](https://isb-cgc.appspot.com)  --  this is all you need to do in order to your Google identity registered as one of our end-users.  Once you are signed in, you can request a GCP if you don't already have one.  

Once you have a GCP, you will need to enable Compute Engine and Deployment Manager and install the Cloud SDK locally.  (See steps 2 and 3 in this [Quickstart guide](https://cloud.google.com/deployment-manager/quickstart-guide)).

A recently introduce alternative to installing the Cloud SDK locally is to use the [Google Cloud Shell](https://cloud.google.com/cloud-shell/docs/) feature that is now available directly from the Google Cloud [Console Dashboard](https://console.developers.google.com/home/dashboard).  In the upper-right corner, next to your project name, clicking on the **[>_]** icon will activate Google Cloud Shell.  Cloud Shell will come pre-installed with Cloud SDK which you can verify by typing ``glcoud --version`` at the shell command line.  Note that Cloud Shell is not intended for large compute jobs, and comes with only 5 GB of persistent disk storage -- instead it is intended as a central (and persistent) location from which you can manage your GCE instances, manage data in Cloud Storage, interact with git repositories, *etc*.

If you are new to using the Google Cloud, once you've installed the Cloud SDK, you'll want to become familiar with two important command-line tools:
* [gcloud](https://cloud.google.com/sdk/gcloud/) for managing your GCP resources; and
* [gsutil](https://cloud.google.com/storage/docs/gsutil?hl=en) for access to Google Cloud Storage (GCS) from the command line.

You can check your current configuration using ``gcloud config list`` where in particular you'll want to double-check that the values for account and project are correct.  If you are using an ISB-CGC project, it will have a name like ``isb-cgc-mm-nnnn`` and will probably be automatically set correctly unless you are a member of multiple GCPs.  You will probably need to set your default region and zone for GCE using the **gcloud** command.  (For help, type ``gcloud config --help``.)

```
gcloud config set project <your-project-name>
gcloud config set compute/zone us-central1-c
```

Note that you may need to run ``gcloud auth login`` to authenticate yourself (although this is never necessary when inside the Cloud Shell since you will be automatically authenticated when you launch it).

Your home directory should be ``/home/<your-user-name>`` and you may want to create a subdirectory for any github repos you plan to clone, including this one:

```
mkdir -p git_home/isb-cgc
cd git_home/isb-cgc
git clone https://github.com/isb-cgc/examples-Compute.git
```

If you have previously cloned this repository and just want to check for new updates, do this:
```
cd ~/git_home/isb-cgc/examples-Compute
git pull
```

If you are new to github, this [simple guide](http://rogerdudler.github.io/git-guide/) is a good place to start and there are many other [references](https://help.github.com/articles/good-resources-for-learning-git-and-github/) available on-line.

##CWL Deployment Template Parameters

The template parameters can be found in ``examples-Compute/cwl-deployment/cwl-node.yaml`` under "properties":

- **containerVmName**:  The name of the container VM image to use; currently set to use "container-vm-v20151215".  More information about container-optimized VM images can be found [here](https://cloud.google.com/compute/docs/containers/container_vms), and an up-to-date list of available VM images can be found by running "gcloud compute images list".  (The v20151215 image includes docker 1.8.3 and kubelet 1.1.3)

- **zone**:  The compute zone you'd like to create your instance and disks in; currently set to use "us-central1-c".  More information about GCE Regions and Zones can be found [here](https://cloud.google.com/compute/docs/zones?hl=en).  You should choose a "us-central" or "us-east" zone regardless of your actual location.  Note that different [machine types](https://cloud.google.com/compute/docs/machine-types) are available in different zones.  Also note that all ISB-CGC hosted data is in [Standard Storage](https://cloud.google.com/storage/docs/standard-storage) in the US.

- **machineType**:  The type of machine you'd like to use for your deployment; currently set to "n1-highmem-16".  For a complete list of images and their specifications, see [Google Compute Engine Machine Types](https://cloud.google.com/compute/docs/machine-types).

- **bootDiskSizeGb**:  The size of the boot disk for the VM in gigabytes; currently set to "500".

- **bootDiskType**:  The type of boot disk to use, which can be one of "pd-standard", "pd-ssd" or "local-ssd"; currently set to "pd-standard".  For more information about block storage, see [Google Compute Engine Block Storage](https://cloud.google.com/compute/docs/disks).

- **startupScript**:  The startup script to run on the VM when it boots for the first time; currently set to point to the script "cwl-node-startup.sh" in this directory.

- **serviceAcctEmail**:  The service account email to use; currently set to "default". 

The "name" of the VM (listed under "resources") may also be changed as well.  This will be the name of the VM that's created for you as part of the deployment, and can be used to access the VM using the "gcloud" tool.  

Any of the above values can be modified to suit your needs.  However, it should be noted that the above settings were developed with the examples in mind, so change them only if you know what you are doing.

##Creating the deployment

Once you're satisfied with your template, you can create your deployment using the [Google Cloud Deployment Manager](https://cloud.google.com/deployment-manager/overview):
```
cd examples-Compute/cwl-deployment
gcloud deployment-manager deployments create <deployment-name> --config cwl-node.yaml
```
You can name your deployment anything you want, for example ``my-cwl-deployment``.  The deployment should only take a few seconds, after which you should see something like this:
```
Waiting for create operation-1451593204105-528376149ff28-e4c3b5ee-1dff694f...done.
Create operation operation-1451593204105-528376149ff28-e4c3b5ee-1dff694f completed successfully.
NAME      TYPE                 STATE      ERRORS
cwl-node  compute.v1.instance  COMPLETED  -
```
Note that the name of the VM (``cwl-node``) that you have created is different from the name of the *deployment* given as part of the ``create`` command.  The VM name was specified in the ``cwl-node.yaml`` file.
You can list your existing deployments using the ``gcloud deployment-manager deployments list`` command, and you can use the ``describe`` command to get more information about a specific deployment:
```
dr_breteuil@isb-cgc-01-0001:~/git_home/examples-Compute/cwl-deployment$ gcloud deployment-manager deployments describe my-cwl-deployment
fingerprint: HnoYlFuZSbgmSC5NLrvgmw==
id: '5688817377067152155'
insertTime: '2015-12-31T12:20:04.297-08:00'
manifest: https://www.googleapis.com/deploymentmanager/v2/projects/isb-cgc-01-0001/global/deployments/my-cwl-deployment/manifests/manifest-145159320430
2
name: my-cwl-deployment
operation:
  endTime: '2015-12-31T12:20:44.931-08:00'
  id: '6459024288776729371'
  kind: deploymentmanager#operation
  name: operation-1451593204105-528376149ff28-e4c3b5ee-1dff694f
  operationType: insert
  progress: 100
  startTime: '2015-12-31T12:20:04.476-08:00'
  status: DONE
  targetId: '5688817377067152155'
  targetLink: https://www.googleapis.com/deploymentmanager/v2/projects/isb-cgc-01-0001/global/deployments/my-cwl-deployment
  user: dr.breteuil@gmail.com
  warnings:
  - data:
    - key: disk_size_gb
      value: '500'
    - key: image_size_gb
      value: '10'
    message: 'Disk size: ''500 GB'' is larger than image size: ''10 GB''. The primary
      root persistent disk partition size will be equal to the image size. The disk
      needs to be re-partitioned from within an instance before the additional space
      can be used.'
resources:
NAME      TYPE                 STATE      ERRORS
cwl-node  compute.v1.instance  COMPLETED  -
```

Once you have successfully deployed, you can ssh to this new VM:
```
gcloud compute ssh cwl-node
```
You will be prompted to generate SSH keys, with an optional passphrase.  Once you are logged in to the cwl-node VM, your prompt should look like ``<user-name>@cwl-node:~$`` rather than ``<user-name>@<project-id>:`` which was your prompt in the Cloud Shell.  You now have a much more powerful VM with more disk and more RAM at your disposal.  

You can see this VM from the [Google Console](https://console.developers.google.com/home/dashboard) under Compute Engine > VM instances.  From the Console dashboard, you can "STOP" and "DELETE" VM instances, see the machine's IP address and SSH directly to it.

The ``cwl-node-startup.sh`` script created a Unix group called ``docker``, and in order to run the sample workflows, you will need to add your user id to this group and restart the docker service.  This will be a one-time operation on this VM:
```
sudo gpasswd -a ${USER} docker
newgrp docker
```
You can use ``echo $USER`` or ``whoami`` to verify your username.  Now, restart docker:
```
sudo service docker stop ; sleep 5s; sudo service docker start
```
(Note that ``sudo service docker restart`` should work, but might fail, hence the inelegant suggestion above.)

##Clean up

Once you are done with your deployment, make sure to delete it to avoid being charged for resources.  In general, it is best practice to delete unused resources to save costs and free up quota.

To delete the deployment (and the underlying VM), run:
```
gcloud deployment-manager deployments delete my-cwl-deployment
```


