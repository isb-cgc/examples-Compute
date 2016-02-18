#ISB-CGC Workflow Examples 

`isb-cgc-workflows.py` is a command line tool for running pre-coded workflows on Kubernetes.  Currently, the following workflows are supported:
- samtools-index
- fastqc

More pre-coded workflows will be added in the future, so check often for updates.

## Setup

The general method for getting set up to run workflows using `isb-cgc-workflows.py` is as follows:
- Follow all of the required setup steps outlined in the [workflow runner README](../../README.md).
- Authenticate to Google by running `gcloud auth login` on your workstation and following all prompts.
- Source the "toil" python virtual environment created by running the [workstation setup script](../../workstation_setup.sh):
```
source ~/virtualenv/toil/bin/activate
```
- Make sure the Kubernetes workflow runner classes are appended to the PYTHONPATH variable:
```
export PYTHONPATH=$PYTHONPATH:/home/<user>/examples-Compute/kubernetes
```

## Command Structure

The command structure for running workflows using `isb-cgc-workflows.py` is as follows:

```
python isb-cgc-workflows.py [global-args] WORKFLOW_NAME [workflow-args]
```
The following global arguments are required for every workflow:
- project_id
- zone
- nodes
- cluster_node_disk_size
- cluster_nfs_volume_size
- machine_type

For descriptions of each argument, run `python isb-cgc-workflows.py -h`.

Workflow names and arguments will be explained in detail in the following sections.

### Running the `samtools-index` workflow

To run the example `samtools-index` workflow, run the following command:

```
python isb-cgc-workflows.py [global-args] samtools-index --input_files open-access-bam-files.txt --output_bucket gs://my-bucket/destination
```

The `--input_files` flag allows you to specify a path to a list of GCS URLs, one per line, each representing a single input file to process.
The `--output_bucket` flag allows you to specify a GCS output bucket (or directory object) URL for uploading the results files.  If not provided, the results will follow the same object hierarchy of the original input file; therefore, unless you have WRITE permissions on the location of the original object, you must specify an output destination for your results.

### Running the `fastqc` workflow

To run the example `fastqc` workflow, run the following command:

```
python isb-cgc-workflows.py [global-args] fastqc --input_files open-access-bam-files.txt --output_bucket gs://my-bucket/destination
```

The `--input_files` flag allows you to specify a path to a list of GCS URLs, one per line, each representing a single input file to process.
The `--output_bucket` flag allows you to specify a GCS output bucket (or directory object) URL for uploading the results files.  If not provided, the results will follow the same object hierarchy of the original input file; therefore, unless you have WRITE permissions on the location of the original object, you must specify an output destination for your results.
