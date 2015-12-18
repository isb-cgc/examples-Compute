#!/usr/bin/env cwl-runner

class: CommandLineTool
description: ""

requirements:
  - class: DockerRequirement
    dockerPull: nasuno/samtools
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
          script: $job['fasta_sequence'].path.split('/').slice(-1)[0]
        fileContent:
          engine: "#node_engine"
          script: $job['fasta_sequence']
    
inputs:
  - id: "#fasta_sequence"
    type: File
    
outputs:
  - id: "#indexed_fasta_sequence"
    type: 
      type: array
      items: File
    outputBinding: 
      glob: 
        engine: "#node_engine"
        script: $job['fasta_sequence'].path.split('/').slice(-1)[0] + "*" 
  - id: "#stdout"
    type: File
    outputBinding:
      glob: samtools-faidx.out

baseCommand: ["samtools", "faidx"]
arguments: 
  - valueFrom: 
      engine: "#node_engine"
      script: $job['fasta_sequence'].path.split('/').slice(-1)[0]
    position: 1
stdout: samtools-faidx.out
