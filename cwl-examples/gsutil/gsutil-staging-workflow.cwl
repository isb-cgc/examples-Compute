#!/usr/bin/env cwl-runner

class: Workflow
description: "Stages files from GCS to a local disk for further processing"

requirements:
  - import: gcs-schema-def.yml
  - class: ScatterFeatureRequirement

inputs:
  - id: "#file_mappings"
    type:
      type: array
      items: "gcs-schema-def.yml#gcs_url_to_file_mapping"
#  - id: "#fasta"
#    type: "gcs-schema-def.yml#gcs_url_to_file_mapping"
#  - id: "#gtf"
#    type: "gcs-schema-def.yml#gcs_url_to_file_mapping"
#  - id: "#bam"
#    type: "gcs-schema-def.yml#gcs_url_to_file_mapping"

outputs:
  - id: "#staged_files"
    type: 
      type: array
      items: File
    source: "#get_file.output"

steps:
  - id: "#get_file"
    run: { import: gsutil-cp/gsutil-cp.cwl }
    scatter: "#get_file.file_url_and_destination"
    inputs: 
      - { id: "#get_file.file_url_and_destination", source: "#file_mappings" }
    outputs:
      - { id: "#get_file.output" }

