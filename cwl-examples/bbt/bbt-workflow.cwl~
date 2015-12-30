#!/usr/bin/env cwl-runner

class: Workflow
description: ""

# Steps:
# Get fasta sequence 
# Index the fasta sequence
# Generate a bloom filter
# Categorize reads based on bloom filter

requirements:
  - class: ScatterFeatureRequirement
  
inputs:
  - id: "#biobloommaker_output_prefix"
    type: string
  - id: "#filter_fasta_sequence_file"
    type: File  
  - id: "#biobloomcategorizer_output_prefix"
    type: string
  - id: "#input_sequence"
    type: File

outputs:
  - id: "#categorized_reads"
    type: 
      type: array
      items: File
    source: "#categorize_reads.categorized_reads"
    

steps:
  - id: "#index_fasta_files"
    run: { import: ../samtools/samtools-faidx.cwl }
    inputs: 
      - { id: "#index_fasta_files.fasta_sequence", source: "#filter_fasta_sequence_file" }
    outputs:
      - { id: "#index_fasta_files.indexed_fasta_sequence" }
      - { id: "#index_fasta_files.stdout" }
  
  - id: "#generate_bloom_filters"
    run: { import: biobloommaker/biobloommaker.cwl }
    inputs: 
      - { id: "#generate_bloom_filters.output_prefix", source: "#biobloommaker_output_prefix" }
      - { id: "#generate_bloom_filters.filter_fasta_sequence", source: "#index_fasta_files.indexed_fasta_sequence" }
    outputs:
      - { id: "#generate_bloom_filters.filter_files" }
      - { id: "#generate_bloom_filters.stdout" }

  - id: "#categorize_reads"
    run: { import: biobloomcategorizer/biobloomcategorizer.cwl }
    inputs:
      - { id: "#categorize_reads.output_prefix", source: "#biobloomcategorizer_output_prefix" }
      - { id: "#categorize_reads.filter_files", source: "#generate_bloom_filters.filter_files" }
      - { id: "#categorize_reads.input_sequence", source: "#input_sequence" }
    outputs:
      - { id: "#categorize_reads.categorized_reads" }
      - { id: "#categorize_reads.stdout" }

