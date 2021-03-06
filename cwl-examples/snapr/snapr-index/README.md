#SNAPR Genome Index Generation CommandLineTool

The SNAPR Genome Index Generation CommandLineTool generates a genome index from a given FASTA file. 

##Prerequisites

Before running the SNAPR Genome Index Generation CommandLineTool, you will want to run the data staging workflow to grab the example files from Google Cloud Storage.  That example files and README can be found in the [gsutil examples folder](../../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [snapr-index-inputs.json](./snapr-index-inputs.json) to reflect this.

##Running the tool

To run the genome index generation tool, run the following command in this directory:

```
cwl-runner snapr-index.cwl snapr-index-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner snapr-index.cwl snapr-index-inputs.json
```

For more information about SNAPR, refer to the [documentation](https://price.systemsbiology.org/research/snapr). 


