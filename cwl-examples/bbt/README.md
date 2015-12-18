#BioBloomTools (BBT) Workflow

_**From the [BCGSC BioBloomTools software page](http://www.bcgsc.ca/platform/bioinfo/software/biobloomtools):**_
> BioBloom Tools (BBT) provides the means to create filters for a given reference and then to categorizes sequences. This methodology is faster than alignment but does not provide mapping locations. BBT was initially intended to be used for pre-processing and QC applications like contamination detection, but is flexible to accommodate other purposes.

##Directory Structure
```
bbt/
  bbt-workflow.cwl  (Workflow)
  bbt-workflow-inputs.json  (Workflow inputs)
  biobloommaker/
    biobloommaker.cwl  (CommandLineTool)
    biobloommaker-inputs.json  (CommandLineTool inputs, for reference/testing only)
  biobloomcategorizer/
    biobloomcategorizer.cwl  (CommandLineTool)
    biobloomcategorizer-inputs.json  (CommandLineTool inputs, for reference/testing only)
```

##Workflow Steps
The BBT Workflow has 3 steps:
- FASTA Indexing ([samtools-faidx](../samtools/samtools-faidx))
- Bloom Filter Creation ([biobloommaker](./biobloommaker))
- Categorizing Reads ([biobloomcategorizer](./biobloomcategorizer))

FASTA indexing is an independent step.  Bloom filter creation depends on the successfull creation of the FASTA index, and read categorization depends on the successful creation of the bloom filter files.

##Running the Workflow
Before running the BBT workflow, you will need to run the data staging workflow to grab the example files from Google Cloud Storage.  The example files and README can be found in the [gsutil examples folder](../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply update the paths in [bbt-workflow-inputs.json](./bbt-workflow-inputs.json) to reflect this.

To run the BBT workflow, run the following command in this directory:

```
cwl-runner bbt-workflow.cwl bbt-workflow-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner bbt-workflow.cwl bbt-workflow-inputs.json
```

For more information about BBT, refer to the [documentation](https://github.com/bcgsc/biobloom/).
