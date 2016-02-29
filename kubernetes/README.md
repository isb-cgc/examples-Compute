#ISB-CGC Workflow Examples 

`IsbCgcWorkflows.py` is a command line tool for running pre-coded workflows on Kubernetes.  Currently, the following workflows are supported:
- samtools-index: Runs `samtools index` on a list of BAM files
- qc: Runs `fastqc` and `picard` on a list of fastq and/or BAM files

More pre-coded workflows will be added in the future, so check often for updates.

## Prerequisites

Before you get started running workflows with `IsbCgcWorkflows.py`, you need to be sure of the following:
* You are a member of a Google Cloud Project and have "Owner" or "Editor" rights
* You have enabled the following APIs in your Google Cloud Project: Google Compute Engine, Google Container Engine, Google Cloud Logging
* If you want to access ISB-CGC data (open or controlled), you must also register as a user through our webapp.  (more info coming soon!)
* If you want to access ISB-CGC controlled data, you must also possess dbGaP authorization and link your eRA Commons identity with your ISB-CGC identity. (more info coming soon!)

It is also recommended to read the following ISB-CGC documentation in order to learn more about using Google Compute Engine and how it fits within the ISB-CGC computational model:
* Google Compute Engine 101 (link coming soon!)
* Google Developer's Console 101 (link coming soon!)
* ISB-CGC Computational Model (link coming soon!)

## Setup

Once you have met the prerequisites above, follow these setup steps to prepare your workstation:
- Create Google Compute Engine VM instance for your workstation in your Google Cloud Project:
```
gcloud compute instances create isb-cgc-workflows --machine-type n1-standard-4 --metadata startup-script-url="https://raw.githubusercontent.com/isb-cgc/examples-Compute/develop/kubernetes/scripts/setup/workstation_startup.sh" --scopes https://www.googleapis.com/auth/compute,https://www.googleapis.com/auth/devstorage.full_control
```
- SSH to the workstation and run the workstation setup script:
```
gcloud compute ssh isb-cgc-workflows
>> git clone https://github.com/isb-cgc/examples-Compute.git
>> cd examples-Compute/kubernetes/scripts/setup
>> ./workstation_setup.sh
```
- Authenticate to Google by running `gcloud auth login` on your workstation and following all prompts.
- Source the "toil" python virtual environment created by running the [workstation setup script](./scripts/setup/workstation_setup.sh):
```
source ~/virtualenv/toil/bin/activate
```
- Make sure the Kubernetes workflow runner classes are appended to the PYTHONPATH variable:
```
export PYTHONPATH=$PYTHONPATH:$HOME/examples-Compute/kubernetes/lib
```

## Command Structure

The command structure for running workflows using `IsbCgcWorkflows.py` is as follows:

```
python IsbCgcWorkflows.py [global-args] WORKFLOW_NAME [workflow-args]
```
The following global arguments are required for every workflow:
- project_id
- zone
- nodes
- cluster_node_disk_size
- cluster_nfs_volume_size
- machine_type

For descriptions of each argument, run `python IsbCgcWorkflows.py -h`.

Workflow names and arguments will be explained in detail in the following sections.

### Running the `samtools-index` workflow

To run the example `samtools-index` workflow, run the following command:

```
python IsbCgcWorkflows.py [global-args] samtools-index --input_files open-access-bam-files.txt --output_bucket gs://my-bucket/destination
```

The `--input_files` flag allows you to specify a path to a list of GCS URLs, one per line, each representing a single input file to process.
The `--output_bucket` flag allows you to specify a GCS output bucket (or directory object) URL for uploading the results files.  If not provided, the results will follow the same object hierarchy of the original input file; therefore, unless you have WRITE permissions on the location of the original object, you must specify an output destination for your results.

### Running the `qc` workflow

To run the example `qc` workflow, run the following command:

```
python IsbCgcWorkflows.py [global-args] qc --input_files open-access-bam-files.txt --output_bucket gs://my-bucket/destination
```

The `--input_files` flag allows you to specify a path to a list of GCS URLs, one per line, each representing a single input file to process.
The `--output_bucket` flag allows you to specify a GCS output bucket (or directory object) URL for uploading the results files.  If not provided, the results will follow the same object hierarchy of the original input file; therefore, unless you have WRITE permissions on the location of the original object, you must specify an output destination for your results.
