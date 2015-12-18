#!/usr/bin/env cwl-runner

class: CommandLineTool

requirements:
  - class: DockerRequirement
    dockerPull: isbdcampbell/snapr_1.0dev57_v4

inputs:
  - id: "#gene_set"
    type: File
    inputBinding:
      position: 1

  - id: "#fasta_sequence"
    type: File
    inputBinding:
      position: 2

  - id: "#transcriptome_index_dir"
    type: string
    default: "transcriptome-index"
    inputBinding:
      position: 3


outputs:

  - id: "#genome"
    type: File
    outputBinding: 
      glob: transcriptome-index/Genome

  - id: "#genome_index"
    type: File
    outputBinding:
      glob: transcriptome-index/GenomeIndex

  - id: "#genome_index_hash"
    type: File
    outputBinding:
      glob: transcriptome-index/GenomeIndexHash

  - id: "#overflow_table"
    type: File
    outputBinding:
      glob: transcriptome-index/OverflowTable

  - id: "#stdout"
    type: File
    outputBinding:
      glob: snapr-transcriptome.out


baseCommand: ["snapr", "transcriptome"]
arguments:
  - valueFrom: "-O1000"
    position: 4

stdout: snapr-transcriptome.out
