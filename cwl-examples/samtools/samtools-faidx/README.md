#SAMtools (faidx) CommandLineTool

The SAMtools faidx CommandLineTool can be used to create an index for a given FASTA file. 

##Prerequisites

Before running the SAMtools faidx tool, you will need to run the data staging workflow to grab the example files from Google Cloud Storage.  The example files and README can be found in [bioinformatics-pipelines/cwl-examples/gsutil](../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [samtools-faidx-inputs.json](./samtools-faidx-inputs.json) to reflect this.

##Running the tool
To run the SAMtools faidx tool, run the following command in this directory:

```
cwl-runner samtools-faidx.cwl samtools-faidx-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner samtools-faidx.cwl samtools-faidx-inputs.json
```

For more information about SAMtools, refer to the [documentation](http://www.htslib.org/doc/samtools.html).
