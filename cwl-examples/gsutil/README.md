#gsutil Data Staging Workflow

This workflow stages the files needed for the examples from Google Cloud Storage to a location on the local file system.

The gsutil CWL Workflow example has the following directory structure:
```
gsutil/
  gsutil-staging-workflow.cwl  (Workflow)
  <example-files-list>.json  (Workflow inputs, i.e. "snapr-example-files.json", or "bbt-example-files.json")
  gcs-schema-def.yml (User defined data type specification)
  gsutil-cp/
    gsutil-cp.cwl  (CommandLineTool)
    gsutil-cp-inputs.json  (CommandLineTool inputs, for reference/testing only)
```

To run the data staging workflow, run the following command in this directory:

```
sudo cwl-runner gsutil-staging-workflow.cwl <example-files-list>.json
```

Note that some files are duplicated across different examples.  You may wish to remove duplicates from the example file lists if you plan on running more than one of the examples on the same machine.
