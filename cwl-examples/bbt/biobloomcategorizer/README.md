#BBT BioBloomCategorizer CommandLineTool

The BBT BioBloomCategorizer CommandLineTool categorizes reads given a set of bloom filters.

##Prerequisites

Before running the BBT BioBloomCategorizer CommandLineTool, you will need to run the data staging workflow to grab the example files from Google Cloud Storage.  That example files and README can be found in the [gsutil examples folder](../../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [biobloomcategorizer-inputs.json](./biobloomcategorizer-inputs.json) to reflect this.

You will also need to generate the FASTA index for the input FASTA file. The FASTA index generation example files and README can be found in either the [samtools-faidx example folder](../../samtools/samtools-faix), or the [fastahack example folder](../../fastahack).

You will also need to generate the required bloom filters to categorize on.  The bloom filter generation example files and README can be found in the [biobloommaker example folder](../biobloommaker).

##Running the tool

To run the biobloommaker tool, first link the original FASTA file, FASTA index and bloom filter files (.bf and .txt) created in the previous workflow steps in /cwl-data/workflows/bbt/inputs respectively, and run the following command in this directory:

```
cwl-runner biobloommaker.cwl biobloommaker-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner biobloommaker.cwl biobloommaker-inputs.json
```

For more information about BBT, refer to the [documentation](https://github.com/bcgsc/biobloom/).
