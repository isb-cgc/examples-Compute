#SNAPR Single-End Alignment CommandLineTool

The SNAPR Single-End Alignment CommandLineTool aligns single-end reads to BAM format.

##Prerequisites
Before running the SNAPR Single-End Alignment CommandLineTool, you will need to run the data staging workflow to grab the example files from Google Cloud Storage.  That example files and README can be found in the [gsutil examples folder](../../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [snapr-single-alignment-inputs.json](./snapr-single-alignment-inputs.json) to reflect this.

You will also need to generate the genome and transcriptome indices before running an alignment.  The genome index generation example files and README can be found in the [snapr-index example folder](/../snapr-index), and the transcriptome index generation example files and README can be found in the [snapr-transcriptome example folder](/../snapr-transcriptome).

##Running the tool

To run the single-end alignment tool, first link the genome-index and transcriptome-index directories created in the previous workflow steps to /cwl-data/workflows/snapr/inputs/genome-index and /cwl-data/workflows/snapr/inputs/transcriptome-index respectively, and run the following command in this directory:

```
cwl-runner snapr-single-alignment.cwl snapr-single-alignment-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner snapr-single-alignment.cwl snapr-single-alignment-inputs.json
```

For more information about SNAPR, refer to the [documentation](https://price.systemsbiology.org/research/snapr). 


