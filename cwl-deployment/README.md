#ISB-CGC Single-Node Workflow Deployment

This directory contains files that you can use to create a deployment for running CWL workflows on a single Google Compute Engine VM.  

##Template Parameters

The template parameters can be found in cwl-node.yaml under "properties", and consist of the following values:
- containerVmName:  The name of the container VM image to use; currently set to use "container-vm-v20151103".  Images are subject to deprecation, so be sure to check the output of "gcloud compute images list" for an up-to-date list of available container-optimized VM images.
- zone:  The compute zone you'd like to create your instance and disks in; currently set to use "us-central1-c".
- machineType:  The type of machine you'd like to use for your deployment; currently set to "n1-highmem-16".  For a complete list of images and their specifications, see [Google Compute Engine Machine Types](https://cloud.google.com/compute/docs/machine-types).
- bootDiskSizeGb:  The size of the boot disk for the VM in gigabytes; currently set to "500".
- bootDiskType:  The type of boot disk to use, which can be one of "pd-standard", "pd-ssd" or "local-ssd"; currently set to "pd-standard".  Fore more information about block storage, see [Google Compute Engine Block Storage](https://cloud.google.com/compute/docs/disks).
- startupScript:  The startup script to run on the VM when it boots for the first time; currently set to point to the script "cwl-node-startup.sh" in this directory.
- serviceAcctEmail:  The service account email to use; currently set to "default". 

The "name" of the VM (listed under "resources") may also be changed as well.  This will be the name of the VM that's created for you as part of the deployment, and can be used to access the VM using the "gcloud" tool.  

Any of the above values can be modified to suit your needs.  However, it should be noted that the above settings were developed with the examples in mind, so change them only if you know what you are doing.

##Creating the deployment

Once you're satisfied with your template, you can create your deployment by completing the following steps:

1) Complete steps 1-3 listed on the [Cloud Deployment Manager Getting Started Guide](https://cloud.google.com/deployment-manager/quickstart-guide).  
2) Set your Google Cloud Project in your gcloud configuration:
```
gcloud config set project <cloud-project-name>
```
3) Authenticate to GCP by running the following command and following all prompts:
```
gcloud auth login
```
4) Create the deployment:
```
cd bioinformatics-pipelines/cwl-deployment
gcloud deployment-manager deployments create <deployment-name> --config cwl-node.yaml
```

5) If the deployment was created successfully, you should be able to ssh to your VM to start playing with the examples by running:
```
gcloud compute ssh <VM-name>
```


