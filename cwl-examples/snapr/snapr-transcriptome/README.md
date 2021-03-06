#SNAPR Transcriptome Index Generation CommandLineTool

The SNAPR Transcriptome Index Generation CommandLineTool generates a transcriptome index from a given FASTA file and Gene Set file.

##Prerequisites

Before running the SNAPR Transcriptome Index Generation CommandLineTool, you will want to run the data staging workflow to grab the example files from Google Cloud Storage.  That example files and README can be found in the [gsutil examples folder](../../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [snapr-transcriptome-inputs.json](./snapr-transcriptome-inputs.json) to reflect this.

##Running the tool

To run the transcriptome index generation tool, run the following command in this directory:

```
cwl-runner snapr-transcriptome.cwl snapr-transcriptome-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner snapr-transcriptome.cwl snapr-transcriptome-inputs.json
```

For more information about SNAPR, refer to the [documentation](https://price.systemsbiology.org/research/snapr).  


