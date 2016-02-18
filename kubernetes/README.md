#ISB-CGC Kubernetes Examples

## Setup

Before you get started running workflows, you need to be sure of the following:
* You are a member of a Google Cloud Project and have "Owner" or "Editor" rights
* You have enabled the following APIs in your Google Cloud Project: Google Compute Engine, Google Container Engine, Google Cloud Logging
* If you want to access ISB-CGC data (open or controlled), you must also register as a user through our webapp.  (more info coming soon!)
* If you want to access ISB-CGC controlled data, you must also possess dbGaP authorization and link your eRA Commons identity with your ISB-CGC identity. (more info coming soon!)

It is also recommended to read the following ISB-CGC documentation in order to learn more about using Google Compute Engine and how it fits within the ISB-CGC computational model:
* Google Compute Engine 101 (link coming soon!)
* Google Developer's Console 101 (link coming soon!)
* ISB-CGC Computational Model (link coming soon!)

This directory contains all that you need to setup and run a containerized workflow on Google Container Engine (Kubernetes):
* workstation_setup.sh - This script will install all of the workflow runner dependencies on your workstation.  It's highly recommended that you use a Google Compute Engine VM for your workstation.  For general information about setting up an ISB-CGC compute workstation, see our Google Compute Engine 101 document. (link coming soon!)
* KubernetesWorkflowRunner.py - This file contains the workflow runner class.  You can import this class into a Python script in order to generate workflows completely programmatically.
* KubernetesToilJobs.py - This file contains additional classes that the workflow runner class uses to build the job graph.
* examples/json - This directory contains some sample JSON formatted schemas that you can run as workflows from the command line (see "Running a workflow" below).
* examples/scripts - This directory contains some sample scripts illustrating how you could generate and run a workflow completely programmatically (see "Running a workflow" below)

## Specifying a workflow

The workflow runner class accepts a python object matching the following schema:
```
{
  "name": string,                     # required; the name of the workflow
  "cluster": {                        # required; the GKE cluster configuration parameters
    "project_id": string,             # required; the GCP project ID where you want to run the workflow
    "zone": string,                   # required; see the Google Compute Engine Regions and Zones documentation for a list of valid choices
    "nodes": int,                     # required; the number of nodes to create in the GKE cluster
    "network": string,                # required; the Google Compute Engine network to use; default value is "default"
    "machine_type": string,           # required; see the Google Compute Engine Machine Types documentation for a list of valid choices
    "cluster_node_disk_size": int,    # required; the size (in gigabytes) of the boot disk for all hosts in the cluster
    "cluster_nfs_volume_size": int,   # required; the size (in gigabytes) of the cluster's shared disk resource
    "tear_down": boolean              # optional; default value is True; when set to False, the cluster will persist beyond the end of the workflow
  },
  "jobs": [                           # required; the job specifications list
    {
      "name": string,                 # required; the name of the job; must be unique
      "container_image": string,      # required; the repository location of the container image to use for this job
      "container_script": string,     # required; the script to run in the container when it starts up
      "parents": array of string,     # optional; a list of strings whose names are other jobs in the "jobs" array; if not provided, the job is assumed to be a root job
      "restart_policy": string        # optional; one of "OnFailure", "Always" or "Never"; default value is "Never"
    },
    ...
  ] 
}
```

The workflow runner class compiles the above schema into a "graph" (specifically a DAG) of containerized processes (aka jobs), which will be posted to the Kubernetes API server on the workflow's dedicated cluster.  Each job in the graph will not start until all of its parents have run to completion.  If a job fails and the restart policy for the job is "Never", the workflow will terminate with an error.


## Designing a workflow

Here are some general guidelines to follow when designing your workflow:
- Start by writing a simple sequential shell script that will contain all of the essential code for running the workflow.  
- In the sequential bash script, identify all "atomic" chunks of code that must be run sequentially.  You can also think of individual iterations of loops in your script as (parametrized) atomic chunks.
- Make modifications to each atomic chunk with respect to known system properties, discussed below in the "Writing container scripts" section.
- Topologically sort the modified atomic chunks of code.  In the workflow specification above, this is expressed in the "parents" attribute within each job.  

## Writing container scripts

### Container Worldview
Every container's working directory contains two subdirectories: `share/` and `scratch/`

The `share/` subdirectory is mounted from an NFS share that exists on the cluster.  This is how you can easily share files between containers.
The easiest way to stage data to `share/` is to use the `gsutil` command in the container `google/cloud-sdk`:

```
if [ ! -f share/my-input-file.txt ]; then
  gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp gs://my-bucket/my-input-file.txt share
fi
```

The `scratch/` subdirectory is mounted from the cluster host, is dynamically allocated and exists only as long as the container is running.  You will get better performance on long running jobs if you stage your data from `share/` to `scratch/` before running the computation.  You will also need to be sure to copy your outputs back to `share/` after the computation has completed, especially if the outputs are needed for downstream processing, and it may also be necessary to periodically clean up files in `share/` that you no longer need to avoid having the shared storage space fill up too quickly.

```
if [ ! -f share/my-results.success ]; then
  cd scratch
  cp ../share/my-input-file.txt .
  <RUN YOUR COMMAND HERE> && touch ../share/my-results.success # produces 'my-results.out', and on success creates 'my-results.success' in the shared directory
  rm ../share/my-input-file.txt
  cp my-results.out ../share
fi
```

Once your computational job ends, you can run another job to copy your results to Google Cloud Storage using the `google/cloud-sdk` container:

```
gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp share/my-results.out gs://my-output-bucket
```

## How to specify a container script

There are two options for specifying a container script to use for a job in a workflow:

1) You can embed it directly in the workflow specification as a single string, made up of a sequence of semi-colon delimited commands.  Bourne Shell is used by default to execute the command string in the container when it runs, so if you want to embed the script inline in the workflow specification document, you must adhere to Bourne Shell syntax.

2) You can store the container scripts in Google Cloud Storage first, and use an extra step in the workflow to stage the script files to the NFS share before they are run.  One benefit of this method is that you can specify the shell interpreter that you want to use at the top of your script file using the "#!/path/to/shell" syntax.  One drawback is that you may also need to alter permissions on the script file to be globally executable before attempting to run it in from another containerized job.


## How to run a workflow

There are two methods for running a workflow:

1) On the command line:

```
gcloud auth login # follow prompts
source ~/virtualenv/toil/bin/activate # this virtualenv was created for you if you ran the workstation setup script in this repo
PYTHONPATH=$PYTHONPATH:~/examples-Compute/kubernetes
python KubernetesWorkflowRunner.py my-workflow-spec.json "/tmp/job_scratch"
```

The main function in KubernetesWorkflowRunner.py takes two parameters: the path to the workflow specification file (JSON) and a path for the runner to use to create a "scratch" space.  The scratch directory must not already exist.  

This method is appropriate for running a workflow using a schema that you generated by hand in a JSON document.  However, if your workflow contains many jobs and would take a long time to generate manually, see method 2 below.

2) In a python script (my-workflow-script.py):

```
import json
from KubernetesWorkflowRunner import KubernetesWorkflowRunner

workflow_spec = {}
job_store = "/tmp/my-workflow-scratch"
# Insert code here for programmatically generating the workflow_spec object
workflow_runner = KubernetesWorkflowRunner(workflow_spec, job_store)
workflow_runner.start()
```

To run the above python script, my-workflow-script.py: 
```
gcloud auth login # follow all prompts
source ~/virtualenv/toil/bin/activate 
PYTHONPATH=$PYTHONPATH:/path/to/examples-Compute/kubernetes 
python my-workflow-script.py [ARGS]
```

Additional programmatic examples can be found in the examples/scripts subdirectory.  

## Monitoring workflow progress

In order to check the status of your job containers, you will need to enable Cloud Logging in your Google Cloud Project.  While your workflow is running, you can easily access the logs by clicking on "Logging" in the Google Developer's Console "Products and Services" menu.  From there, you can select the Container Engine logs you want to view by cluster name and namespace, both of which will share the same name with your specified workflow.  You can also further filter the logs by container name.

For more information about enabling Cloud Logging in the Developer's Console, see our Google Developer's Console 101 document. (link coming soon!)
