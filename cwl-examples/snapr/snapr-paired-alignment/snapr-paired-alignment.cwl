#!/usr/bin/env cwl-runner

# SNAPR Paired End Alignment Tool

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
  - id: "#fusions_reads"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.fusions.reads.fa'

  - id: "#fusions"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.fusions.txt'

  - id: "#gene_id_counts"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.gene_id.counts.txt'

  - id: "#gene_name_counts"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.gene_name.counts.txt'

  - id: "#interchromosomal_fusions"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.interchromosomal.fusions.gtf'

  - id: "#intrachromosomal_fusions"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.intrachromosomal.fusions.gtf'

  - id: "#junction_id_counts"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.junction_id.counts.txt'

  - id: "#junction_name_counts"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.junction_name.counts.txt'

  - id: "#transcript_id_counts"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.transcript_id.counts.txt'

  - id: "#transcript_name_counts"
    type: File
    outputBinding:
      glob:
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.transcript_name.counts.txt'

  - id: "#output_bam"
    type: File
    outputBinding:
      glob: 
        engine: "#node_engine"
        script: $job['output_bam_prefix'] + '.bam'

  - id: "#stdout"
    type: File
    outputBinding:
      glob: snapr-single-end-alignment.out


baseCommand: ["snapr", "paired"]
arguments:
  - valueFrom: 
      engine: "#node_engine"
      script: $job['genome_index_genome'].path.split('/').slice(0, -1).join('/')
    position: 1
  - valueFrom: 
      engine: "#node_engine"
      script: $job['transcriptome_index_genome'].path.split('/').slice(0, -1).join('/')
    position: 2
    
stdout: snapr-paired-end-alignment.out

