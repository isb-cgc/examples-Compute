#ISB-CGC Single-Node CWL Workflow Examples

## Setup

In this directory, you will find a startup script which can be run on a Google Compute Engine VM at creation time.  This startup script will install and configure the VM for running the CWL workflow examples.

Below is an example command that you can run to create an instance using the startup script:
```
gcloud compute instances create cwl-node --zone us-central1-a --image container-vm-v20151215 --image-project google-containers --machine-type n1-highmem-16 --boot-disk-size 500GB --boot-disk-type pd-standard --metadata startup-script-url=https://raw.githubusercontent.com/isb-cgc/examples-Compute/master/cwl-examples/cwl-node-startup.sh
```

For more information about the `gcloud compute instances create` command, see the documentation [here](https://cloud.google.com/sdk/gcloud/reference/compute/instances/create).

## Running the examples
Each subdirectory contains the required code files for a particular CWL (Draft 2) example.  Example directories may include one or more CommandLineTool specifications, a Workflow specification, or both, as well as a JSON-formatted input parameters file for each.  For example, the SNAPR example directory contains a Workflow file (.cwl), a JSON-formatted input parameters file, and additional subdirectories for each CommandLineTool required by the Workflow.  Each CommandLineTool directory contains a CommandLineTool file (.cwl), and a JSON-formatted input parameters file.  For CommandLineTool examples nested below a Workflow, the JSON-formatted input parameters files are used for reference or testing purposes only, and are not processed by the outer Workflow.

Example directory structure:
```
workflow/
  workflow.cwl  (Workflow)
  workflow-inputs.json  (Workflow inputs)
  commandlinetool-1/
    commandlinetool-1.cwl  (CommandLineTool)
    commandlinetool-1-inputs.json  (CommandLineTool inputs, for reference/testing only)
  commandlinetool-2/
    commandlinetool-2.cwl  (CommandLineTool)
    commandlinetool-2-inputs.json  (CommandLineTool inputs, for reference/testing only)
  ...
```
In general, each CommandLineTool represents a single step in the outer Workflow.  For more information about the relationship between CommandLineTool and Workflow, see the [CWL (Draft 2) specification](http://common-workflow-language.github.io/draft-2/).

The general format of the command for running CWL workflows is as follows:
```
cwl-runner [OPTIONS] cwl-workflow.cwl cwl-workflow-inputs.json
```

You can use the "--debug" flag for cwl-runner in order to produce verbose output for troubleshooting issues.  For more information about all of the possible options to cwl-runner, see the [cwl-tool source code](https://github.com/common-workflow-language/cwltool/blob/master/cwltool/main.py).

Once you've created a GCE VM for the examples, you can ssh to it to run them.  Below is a command you can run to connect to the instance that was created in the "Setup" section of this document:
```
gcloud compute ssh cwl-node
```
Once you've created your GCE VM and ssh'ed to it, clone this repo into your home directory so that you can run the examples:
```
git clone https://github.com/isb-cgc/examples-Compute.git
```
