#SNAPR Workflow

_**From the [ISB Price Lab](https://price.systemsbiology.org/research/snapr/):**_

> The growth of next-generation sequencing data now exceeds the growth rate of storage capacity. Researchers’ ability to analyze these data depends upon bioinformatics tools that are fast, accurate, and easy to use. We present SNAPR, a new RNA-seq analysis pipeline designed to handle datasets from a few up to thousands of libraries, while maintaining high alignment accuracy. SNAPR can natively read from and write to BAM format, automatically generate read counts, and identify viral/bacterial infections as well as intra- and inter-chromosomal gene fusions with high accuracy.

##Directory Structure

```
snapr/
  snapr-workflow.cwl  (Workflow)
  snapr-workflow-inputs.json  (Workflow inputs)
  snapr-index/
    snapr-index.cwl  (CommandLineTool)
    snapr-index-inputs.json  (CommandLineTool inputs, for reference/testing only)
  snapr-transcriptome/
    snapr-transcriptome.cwl  (CommandLineTool)
    snapr-transcriptome.json  (CommandLineTool inputs, for reference/testing only)
  snapr-single-end-alignment/
    snapr-single-alignment.cwl  (CommandLineTool)
    snapr-single-alignment-inputs.json  (CommandLineTool inputs, for reference/testing only)
  snapr-paired-end-alignment/
    snapr-paired-alignment.cwl  (CommandLineTool)
    snapr-paired-alignment-inputs.json  (CommandLineTool inputs, for reference/testing only)
```

##Workflow Steps

The SNAPR Workflow example has 4 steps:
- Genome Index Generation ([snapr-index](./snapr-index))
- Transcriptome Index Generation ([snapr-transcriptome](./snapr-transcriptome))
- Single-End Alignment ([snapr-single-alignment](./snapr-single-alignment))
- Paired-End Alignment ([snapr-paired-alignment](./snapr-paired-alignment))

Index generation steps can run independently of one another and alignment steps can run independently of one another, but the alignment steps both depend on the successful completion of both of the index generation steps.

##Prerequisites

Before running the SNAPR workflow, you will want to run the data staging workflow to grab the example files from Google Cloud Storage.  The example files and README can be found in the [gsutil examples folder](../gsutil).  Alternatively, you may also use files on your local filesystem.  Simply use "gcloud compute copy-files ..." to copy local files to your VM, and then update the paths in [snapr-workflow-inputs.json](./snapr-workflow-inputs.json) to reflect this.

##Running the Workflow

To run the SNAPR workflow, run the following command in this directory:

```
cwl-runner snapr-workflow.cwl snapr-workflow-inputs.json
```

For more information about SNAPR, refer to the [documentation](https://price.systemsbiology.org/research/snapr).
