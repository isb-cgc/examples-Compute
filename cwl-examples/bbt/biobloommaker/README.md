#BBT BioBloomMaker CommandLineTool

The BBT BioBloomMaker CommandLineTool creates a bloom filter from an indexed FASTA sequence.

##Prerequisites

Before running the BBT BioBloomMaker CommandLineTool, you will need to run the data staging workflow to grab the example files from Google Cloud Storage.  That example files and README can be found in the [gsutil examples folder](../../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [biobloommaker-inputs.json](./biobloommaker-inputs.json) to reflect this.

You will also need to generate the FASTA index for the input FASTA file. The FASTA index generation example files and README can be found in either the [samtools-faidx example folder](../../samtools/samtools-faix), or the [fastahack example folder](../../fastahack).

##Running the tool

To run the biobloommaker tool, first link the original FASTA file and the FASTA index created in the previous workflow steps in /cwl-data/workflows/bbt/inputs respectively, and run the following command in this directory:

```
cwl-runner biobloommaker.cwl biobloommaker-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner biobloommaker.cwl biobloommaker-inputs.json
```

For more information about BBT, refer to the [documentation](https://github.com/bcgsc/biobloom/).
