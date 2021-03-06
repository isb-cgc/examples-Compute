#!/usr/bin/env cwl-runner

# SNAPR Single End Alignment Tool

class: CommandLineTool

requirements:
  - class: DockerRequirement
    dockerPull: isbdcampbell/snapr_1.0dev57_v4
  - class: ExpressionEngineRequirement
    id: "#node_engine"
    requirements:
      - class: DockerRequirement
        dockerPull: commonworkflowlanguage/nodejs-engine
    engineCommand: cwlNodeEngine.js

inputs:
  - id: "genome_index_genome"
    type: File

  - id: "genome_index_genome_index"
    type: File

  - id: "genome_index_genome_index_hash"
    type: File

  - id: "genome_index_overflow_table"
    type: File

  - id: "transcriptome_index_genome"
    type: File

  - id: "transcriptome_index_genome_index"
    type: File

  - id: "transcriptome_index_genome_index_hash"
    type: File

  - id: "transcriptome_index_overflow_table"
    type: File

  - id: "#output_bam_prefix"
    type: string

  - id: "#gene_set"
    type: File
    inputBinding:
      position: 3

  - id: "#input_bam_file"
    type: File
    inputBinding:
      position: 4

  - id: "#output_bam_file"
    type: string
    inputBinding:
      position: 5
      prefix: "-o"


outputs:
  - id: "#outputs"
    type: 
      type: array
      items: File
    outputBinding:
      glob: 
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + ".*"

  - id: "#stdout"
    type: File
    outputBinding:
      glob: snapr-single-end-alignment.out


baseCommand: ["snapr", "single"]
arguments:
  - valueFrom: 
      engine: "#node_engine"
      script: $job['genome_index_genome'].path.split('/').slice(0, -1).join('/')
    position: 1
  - valueFrom: 
      engine: "#node_engine"
      script: $job['transcriptome_index_genome'].path.split('/').slice(0, -1).join('/')
    position: 2
    
stdout: snapr-single-end-alignment.out

