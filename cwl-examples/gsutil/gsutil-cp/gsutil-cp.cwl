#!/usr/bin/env cwl-runner

class: CommandLineTool
description: "Copies a file from GCS using gsutil"

requirements:
  - import: ../gcs-schema-def.yml
  - class: EnvVarRequirement
    envDef:
      - envName: PATH
        envValue: /bin:/usr/bin:/usr/local/bin:/home/abby/tools/google-cloud-sdk/bin/gsutil   

inputs:
  - id: "#file_url_and_destination"
    type: "../gcs-schema-def.yml#gcs_url_to_file_mapping"
  
outputs:
  - id: "#output"
    type: File
    outputBinding:
      glob: 
        engine: cwl:JsonPointer
        script: /job/file_url_and_destination/destination
    

baseCommand: ["gsutil", "-m", "cp"]
arguments:
  - valueFrom:
      engine: cwl:JsonPointer
      script: /job/file_url_and_destination/url
  - valueFrom:
      engine: cwl:JsonPointer
      script: /job/file_url_and_destination/destination

