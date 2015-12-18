#!/usr/bin/env cwl-runner

class: CommandLineTool
description: ""

requirements:
  - class: DockerRequirement
    dockerPull: gcr.io/isb-cgc/fastahack:v1
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
          engine: cwl:JsonPointer
          script: /job/fasta_sequence
    
inputs:
  - id: "#fasta_sequence"
    type: File

outputs:
  - id: "#indexed_fasta_sequence"
    type: File
    outputBinding: 
      glob: 
        engine: "#node_engine"
        script: $job['fasta_sequence'].path.split('/').slice(-1)[0] + '.fai'

  - id: "#stdout"
    type: File
    outputBinding:
      glob: fastahack-index.out

baseCommand: ["fastahack", "-i"]
arguments: 
  - valueFrom: 
      engine: "#node_engine"
      script: $job['fasta_sequence'].path.split('/').slice(-1)[0]
    position: 1
stdout: fastahack-index.out
