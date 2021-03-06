#!/usr/bin/env cwl-runner

class: Workflow
description: "Generates genome and transcriptome indices from a given FASTA sequence and GTF file, and runs single- and paired-end alignments on a BAM file"

inputs:
  - id: "#fasta_sequence_file"
    type: File
  - id: "#gene_set_file"
    type: File
  - id: "#bam_file"
    type: File
  - id: "#single_alignment_output_bam_file"
    type: string
  - id: "#single_alignment_output_bam_prefix"
    type: string
  - id: "#paired_alignment_output_bam_file"
    type: string
  - id: "#paired_alignment_output_bam_prefix"
    type: string

outputs:
  - id: "#build_genome_index_stdout"
    type: File
    source: "#build_genome_index.stdout"

  - id: "#build_transcriptome_index_stdout"
    type: File
    source: "#build_transcriptome_index.stdout"

  - id: "#single_end_alignment_outputs"
    type: 
      type: array
      items: File
    source: "#run_single_end_alignment.outputs"

  - id: "#stdout"
    type: File
    source: "#run_single_end_alignment.stdout"

steps:
  - id: "#build_genome_index"
    run: { import: snapr-index/snapr-index.cwl }
    inputs: 
      - { id: "#build_genome_index.fasta_sequence", source: "#fasta_sequence_file" }

    outputs:
      - { id: "#build_genome_index.genome" }
      - { id: "#build_genome_index.genome_index" }
      - { id: "#build_genome_index.genome_index_hash" }
      - { id: "#build_genome_index.overflow_table" }
      - { id: "#build_genome_index.stdout" }

  - id: "#build_transcriptome_index"
    run: { import: snapr-transcriptome/snapr-transcriptome.cwl }
    inputs:
      - { id: "#build_transcriptome_index.gene_set", source: "#gene_set_file" }
      - { id: "#build_transcriptome_index.fasta_sequence", source: "#fasta_sequence_file" }

    outputs:
      - { id: "#build_transcriptome_index.genome" }
      - { id: "#build_transcriptome_index.genome_index" }
      - { id: "#build_transcriptome_index.genome_index_hash" }
      - { id: "#build_transcriptome_index.overflow_table" }
      - { id: "#build_transcriptome_index.stdout" }

  - id: "#run_single_end_alignment"
    run: { import: snapr-single-alignment/snapr-single-alignment.cwl }
    inputs:
      - { id: "#run_single_end_alignment.genome_index_genome", source: "#build_genome_index.genome" }
      - { id: "#run_single_end_alignment.genome_index_genome_index", source: "#build_genome_index.genome_index" }
      - { id: "#run_single_end_alignment.genome_index_genome_index_hash", source: "#build_genome_index.genome_index_hash" }
      - { id: "#run_single_end_alignment.genome_index_overflow_table", source: "#build_genome_index.overflow_table" }
      - { id: "#run_single_end_alignment.transcriptome_index_genome", source: "#build_transcriptome_index.genome" }
      - { id: "#run_single_end_alignment.transcriptome_index_genome_index", source: "#build_transcriptome_index.genome_index" }
      - { id: "#run_single_end_alignment.transcriptome_index_genome_index_hash", source: "#build_transcriptome_index.genome_index_hash" }
      - { id: "#run_single_end_alignment.transcriptome_index_overflow_table", source: "#build_transcriptome_index.overflow_table" }
      - { id: "#run_single_end_alignment.output_bam_prefix", source: "#single_alignment_output_bam_prefix" }
      - { id: "#run_single_end_alignment.gene_set", source: "#gene_set_file" }
      - { id: "#run_single_end_alignment.input_bam_file", source: "#bam_file" }
      - { id: "#run_single_end_alignment.output_bam_file", source: "#single_alignment_output_bam_file" }

    outputs: 
      - { id: "#run_single_end_alignment.outputs" }
      - { id: "#run_single_end_alignment.stdout" }
 
