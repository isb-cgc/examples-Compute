#ISB-CGC Grid Engine Example - Index BAM Files by Cohort

This example was based on the example [Run SAMtools to index BAM files in Cloud Storage](http://googlegenomics.readthedocs.org/en/latest/use_cases/run_samtools_over_many_files/index.html) from the [Google Genomics documentation](http://googlegenomics.readthedocs.org/en/latest/index.html).  Be sure to check out some of the other Google Genomics examples, as many of them may be easily adapted to work on your Grid Engine cluster.

###index_bam_files.py

This script is intended to serve as an example illustrating how to work with the ISB-CGC hosted data and metadata.  If you run it with -h you will see the following usage statement:

```
usage: index_bam_files.py [-h] --job_name JOB_NAME --output_bucket
                          OUTPUT_BUCKET --logs_bucket LOGS_BUCKET
                          --grid_computing_tools_dir GRID_COMPUTING_TOOLS_DIR
                          (--cohort_id COHORT_ID | --sample_barcode SAMPLE_BARCODE | --gcs_dir_url GCS_DIR_URL)
                          [--copy_original_bams] [--dry_run]

Index ISB-CGC BAM files by cohort or sample

optional arguments:
  -h, --help            show this help message and exit
  --job_name JOB_NAME   A name for this job.
  --output_bucket OUTPUT_BUCKET
                        The destination bucket for all outputs. Must be a
                        valid Google Cloud Storage bucket URL, i.e.
                        gs://bucket_name. Required
  --logs_bucket LOGS_BUCKET
                        The destination bucket for all logs. Must be a valid
                        Google Cloud Storage bucket URL, i.e.
                        gs://bucket_name. Required
  --grid_computing_tools_dir GRID_COMPUTING_TOOLS_DIR
                        Path to the root directory of the "grid-computing-
                        tools" repository. If you used the grid-engine-master-
                        setup.sh script to install the dependencies, this
                        value should be ~/grid-computing-tools. Required
  --cohort_id COHORT_ID
                        The cohort ID for which you'd like to index associated
                        BAM files.
  --sample_barcode SAMPLE_BARCODE
                        The sample barcode for which you'd like to index
                        associated BAM files.
  --gcs_dir_url GCS_DIR_URL
                        A URL to a directory in GCS to copy files from (rather
                        than going through the API)
  --copy_original_bams  If set, will copy the original bam files from the ISB-
                        CGC cloud storage space to the output bucket.
                        Otherwise a list of the original BAM locations in GCS
                        will be generated in the current working directory.
                        Default: False
  --dry_run             If set, will not copy or index any BAM files, but will
                        display the copy and index operations that would have
                        occurred during a real run. Default: False

```

The idea is that you can specify a set of bam files using one of the following three approaches:
  *  **cohort**:  the ISB-CGC web-app allow syou to define a cohort interactively, or you can use the ISB-CGC programmatic API to define a cohort programmatically;  a cohort is simply a list of patients and samples (typically from the TCGA dataset); or
  *  **sample_barcode**:  if there is just a specific sample you are interested in, you can specify it here (*eg* TCGA-B6-A0RG-01A); or
  *  **gcs_dir_url**:  if you have your own Cloud Storage bucket containing a set of bam files that need indexing, you can specify the bucket url here.


