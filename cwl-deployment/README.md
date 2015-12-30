#ISB-CGC Single-Node Workflow Deployment

This directory contains files that you can use to create a deployment for running CWL workflows on a single Google Compute Engine (GCE) VM (virtual machine).  

##Prerequisites
In order to spin up a GCE VM, you will need access to a Google Cloud project (GCP), and you will also need a local installation of the [Google Cloud SDK](https://cloud.google.com/sdk/).  If you are not yet an ISB-CGC user, please sign-in to the [web-app](https://isb-cgc.appspot.com) and request a GCP if you don't already have one.  Next, you'll need to enable Compute Engine and Deployment Manager and install the Cloud SDK.  (See steps 2 and 3 in this [Quickstart guide](https://cloud.google.com/deployment-manager/quickstart-guide)).

A recently introduce alternative to installing the Cloud SDK locally is to use the [Google Cloud Shell](https://cloud.google.com/cloud-shell/docs/) feature that is now available directly from the Google Cloud [Console Dashboard](https://console.developers.google.com/home/dashboard).  In the upper-right corner, next to your project name, clicking on the **>_** icon will activate Google Cloud Shell.

Once you've installed the Cloud SDK, you'll want to become familiar with two important command-line tools:
* [gcloud](https://cloud.google.com/sdk/gcloud/) for managing your GCP resources; and
* [gsutil](https://cloud.google.com/storage/docs/gsutil?hl=en) for access Google Cloud Storage (GCS) from the command line.

You can check your current configuration using ``gcloud config list`` where in particular you'll want to double-check that the values for account and project are correct.  You can also change your default region and zone for GCE using the **gcloud** command.  (For help, type ``gcloud config --help``.)

```
gcloud config set project <your-project-name>
gcloud config set compute/zone us-central1-c
```

Note that you may need to run ``gcloud auth login`` to authenticate yourself (although this is never necessary when inside the Cloud Shell since you will be automatically authenticated when you launch it).

If you have not already done so, you will need to clone this repo:
```
git clone https://github.com/isb-cgc/examples-Compute.git
```
If you are new to github, this [simple guide](http://rogerdudler.github.io/git-guide/) is a good place to start and there are many other [references](https://help.github.com/articles/good-resources-for-learning-git-and-github/) available on-line.

##CWL Deployment Template Parameters

The template parameters can be found in ``examples-Compute/cwl-deployment/cwl-node.yaml`` under "properties":

- **containerVmName**:  The name of the container VM image to use; currently set to use "container-vm-v20151215".  More information about container-optimized VM images can be found [here](https://cloud.google.com/compute/docs/containers/container_vms), and an up-to-date list of available VM images can be found by running "gcloud compute images list".

- **zone**:  The compute zone you'd like to create your instance and disks in; currently set to use "us-central1-c".  More information about GCE Regions and Zones can be found [here](https://cloud.google.com/compute/docs/zones?hl=en).  You should choose a "us-central" or "us-east" zone regardless of your actual location.  Note that different [machine types](https://cloud.google.com/compute/docs/machine-types) are available in different zones.  Also note that all ISB-CGC hosted data is in [Standard Storage](https://cloud.google.com/storage/docs/standard-storage) in the US.

- **machineType**:  The type of machine you'd like to use for your deployment; currently set to "n1-highmem-16".  For a complete list of images and their specifications, see [Google Compute Engine Machine Types](https://cloud.google.com/compute/docs/machine-types).

- **bootDiskSizeGb**:  The size of the boot disk for the VM in gigabytes; currently set to "500".

- **bootDiskType**:  The type of boot disk to use, which can be one of "pd-standard", "pd-ssd" or "local-ssd"; currently set to "pd-standard".  Fore more information about block storage, see [Google Compute Engine Block Storage](https://cloud.google.com/compute/docs/disks).

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
You can name your deployment anything you want, for example ``my-cwl-deployment``.  The deployment should only take a few seconds, and you should see something like this:
```
Waiting for create operation-1451517181248-52825adf94201-8f0a652b-529ef937...done.
Create operation operation-1451517181248-52825adf94201-8f0a652b-529ef937 completed successfully.
NAME      TYPE                 STATE      ERRORS
cwl-node  compute.v1.instance  COMPLETED  -
```
Next you can use the ``describe`` command to get more information about your deployment:
```
$ gcloud deployment-manager deployments describe my-cwl-deployment
fingerprint: YHeU1pOLbbRD7u2qCX4ghg==
id: '3483907804411582994'
insertTime: '2015-12-30T15:13:01.407-08:00'
manifest: https://www.googleapis.com/deploymentmanager/v2/projects/.../manifests/manifest-145151718141
2
name: my-cwl-deployment
operation:
  endTime: '2015-12-30T15:13:10.574-08:00'
  id: '4872215584381196818'
  kind: deploymentmanager#operation
  name: operation-1451517181248-52825adf94201-8f0a652b-529ef937
  operationType: insert
  progress: 100
  startTime: '2015-12-30T15:13:01.585-08:00'
  status: DONE
  targetId: '3483907804411582994'
  targetLink: https://www.googleapis.com/deploymentmanager/v2/projects/<project-name>/global/deployments/my-cwl-deployment
  user: <your-user-name>
resources:
NAME      TYPE                 STATE      ERRORS
cwl-node  compute.v1.instance  COMPLETED  -
```

Once you have successfully deployed, you can ssh to this new VM:
```
gcloud compute ssh cwl-node
```

##Clean up

Once you are done with your deployment, make sure to delete it to avoid being charged for resources.  In general, it is best practice to delete unused resources to save costs and free up quota.

To delete the deployment, run:
```
gcloud deployment-manager deployments delete my-cwl-deployment
```

