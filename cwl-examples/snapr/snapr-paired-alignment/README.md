#SNAPR Paired-End Alignment CommandLineTool

The SNAPR Paired-End Alignment CommandLineTool aligns paired-end reads to BAM format.

##Prerequisites
Before running the SNAPR Paired-End Alignment CommandLineTool, you will want to run the data staging workflow to grab the example files from Google Cloud Storage.  That example files and README can be found in the [gsutil examples folder](../../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [snapr-paired-alignment-inputs.json](./snapr-paired-alignment-inputs.json) to reflect this.

You will also need to generate the genome and transcriptome indices before running an alignment.  The genome index generation example files and README can be found in [bioinformatics-pipelines/cwl-examples/snapr/snapr-index](/../snapr-index), and the transcriptome index generation example files and README can be found in [bioinformatics-pipelines/cwl-examples/snapr/snapr-transcriptome](/../snapr-transcriptome).

##Running the tool

To run the paired-end alignment tool, first link the genome-index and transcriptome-index directories created in the previous workflow steps to /cwl-data/workflows/snapr/inputs/genome-index and /cwl-data/workflows/snapr/inputs/transcriptome-index respectively, and run the following command in this directory:

```
cwl-runner snapr-paired-alignment.cwl snapr-paired-alignment-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner snapr-paired-alignment.cwl snapr-paired-alignment-inputs.json
```

For more information about SNAPR, refer to the [documentation](https://price.systemsbiology.org/research/snapr).


