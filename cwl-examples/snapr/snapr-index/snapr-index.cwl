#!/usr/bin/env cwl-runner

class: CommandLineTool

requirements:
  - class: DockerRequirement
    dockerPull: isbdcampbell/snapr_1.0dev57_v4

inputs:
  - id: "#fasta_sequence"
    type: File
    inputBinding:
      position: 1
  
  - id: "#genome_index_dir"
    type: string
    default: "genome-index"
    inputBinding: 
      position: 2

outputs:
  - id: "#genome"
    type: File
    outputBinding: 
      glob: genome-index/Genome

  - id: "#genome_index"
    type: File
    outputBinding:
      glob: genome-index/GenomeIndex

  - id: "#genome_index_hash"
    type: File
    outputBinding:
      glob: genome-index/GenomeIndexHash

  - id: "#overflow_table"
    type: File
    outputBinding:
      glob: genome-index/OverflowTable

  - id: "#stdout"
    type: File
    outputBinding:
      glob: snapr-index.out



baseCommand: ["snapr", "index"]
stdout: snapr-index.out
