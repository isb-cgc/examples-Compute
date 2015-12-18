#!/usr/bin/env cwl-runner

class: CommandLineTool
description: "BioBloomTools BioBloomCategorizer tool"

requirements:
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
          script: $job['filter_files'][0].path.split('/').slice(-1)[0]
        fileContent:
          engine: "#node_engine"
          script: $job['filter_files'][0].path.split('/').slice(-1)[0]
      - filename: 
          engine: "#node_engine"
          script: $job['filter_files'][1].path.split('/').slice(-1)[0]
        fileContent:
          engine: "#node_engine"
          script: $job['filter_files'][1].path.split('/').slice(-1)[0]

inputs:
  - id: "#output_prefix"
    type: string
    inputBinding:
      prefix: "-p"
      position: 1
  - id: "#filter_files"
    type: 
      type: array
      items: File
  - id: "#input_sequence"
    type: File
    inputBinding:
      position: 3

outputs:
  - id: "#categorized_reads"
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
      glob: biobloomcategorizer.stdout

baseCommand: ["biobloomcategorizer"]
arguments:
  - valueFrom:
      engine: "#node_engine"
      script: |
        {
          return $job['filter_files'].filter(function isBloomFilter(element) {
            var match_bf = /^.*\.bf$/; 
            return (element.path.search(match_bf) >= 0) || -1; })[0];
        }
    prefix: "-f"
    position: 2
    
stdout: biobloomcategorizer.stdout
