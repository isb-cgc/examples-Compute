#!/usr/bin/env cwl-runner

class: CommandLineTool
description: "BioBloomTools BioBloomMaker tool"

requirements:
  - import: ../biobloomcategorizer/filter-files-schema-def.yml
  - class: DockerRequirement
    dockerPull: gcr.io/isb-cgc/bbt:v2
  - class: ExpressionEngineRequirement
    id: "#node_engine"
    requirements:
      - class: DockerRequirement
        dockerPull: commonworkflowlanguage/nodejs-engine
    engineCommand: cwlNodeEngine.js
  - class: CreateFileRequirement
    fileDef:
      - filename: 
          engine: "#node_engine"
          script: $job['filter_fasta_sequence'][0].path.split('/').slice(-1)[0]
        fileContent:
          engine: "#node_engine"
          script: $job['filter_fasta_sequence'][0].path.split('/').slice(-1)[0]
      - filename: 
          engine: "#node_engine"
          script: $job['filter_fasta_sequence'][1].path.split('/').slice(-1)[0]
        fileContent:
          engine: "#node_engine"
          script: $job['filter_fasta_sequence'][1].path.split('/').slice(-1)[0]
    
inputs:
  - id: "#output_prefix"
    type: string
    inputBinding:
      position: 1
      prefix: "-p"

  - id: "#filter_fasta_sequence"
    type: 
      type: array
      items: File
    
outputs:
  - id: "#filter_files"
    type: 
      type: array
      items: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_prefix'] + "*"
  - id: "#stdout"
    type: File
    outputBinding:
      glob: biobloommaker.stdout
    
baseCommand: ["biobloommaker"]
arguments:
  - valueFrom:
      engine: "#node_engine"
      script: |
        {
          return $job['filter_fasta_sequence'].filter(function isFasta(element) {
            var match_fasta = /^.*\.fa$/; 
            return (element.path.search(match_fasta) >= 0) || -1; })[0];
        }
    position: 2
stdout: biobloommaker.stdout 
