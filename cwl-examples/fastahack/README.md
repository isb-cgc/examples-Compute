#Fastahack CommandLineTool

The Fastahack CommandLineTool can be used to create an index for a given FASTA file, and can be used as an alternative to the SAMtools (faidx) CommandLineTool in the example Workflows. 

##Prerequisites

Before running the Fastahack tool, you will need to run the data staging workflow to grab the example files from Google Cloud Storage.  The example files and README can be found in [bioinformatics-pipelines/cwl-examples/gsutil](../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [fastahack-inputs.json](./fastahack-inputs.json) to reflect this.

##Running the tool

To run the Fastahack tool, run the following command in this directory:

```
cwl-runner fastahack.cwl fastahack-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner fastahack.cwl fastahack-inputs.json
```

For more information about Fastahack, refer to the [documentation](https://github.com/ekg/fastahack).
