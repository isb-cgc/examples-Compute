#Gsutil Copy Tool

This tool copies a single file from Google Cloud Storage to a location on the local file system for use in downstream applications.

To run the gsutil copy tool, run the following command in this directory:

```
cwl-runner gsutil-cp.cwl gsutil-cp-inputs.json
```

Or, if you need sudo privileges to run docker commands:

```
sudo cwl-runner gsutil-cp.cwl gsutil-cp-inputs.json
```
