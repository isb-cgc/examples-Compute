import os
import re
import sys
import json
import pprint
import argparse
import subprocess
from KubernetesWorkflowRunner import KubernetesWorkflowRunner
from random import SystemRandom

class Workflow:
	def __init__(self, cluster):
		self.schema = {
			"name": None,
			"cluster": {
				"project_id": cluster.project_id,
				"zone": cluster.zone,
				"nodes": cluster.nodes,
				"network": "default",
				"machine_type": cluster.machine_type,
				"cluster_node_disk_size": cluster.cluster_node_disk_size,
				"cluster_nfs_volume_size": cluster.cluster_nfs_volume_size
			},
			"jobs": []
		}
		self.dry_run = cluster.dry_run

	def __build(self):
		pass # to be overridden in subclasses

	def __load_script_template(self, path, **params):
		script_lines = []
		with open(path) as f:
			for line in f:
				script_lines.append(line.strip())

		return ';'.join(script_lines).format(**params)

	def __create_subworkflow(self):
		pass # to be overridden in subclasses

	def run(self):
		pprint.pprint(self.schema)
		if not self.dry_run:
			KubernetesWorkflowRunner(self.schema, "/tmp/{workflow}".format(workflow=self.schema["name"])).start()

class SamtoolsIndexWorkflow(Workflow):
	def __init__(self, args, data_staging_script=None, samtools_index_script=None, cleanup_script=None):
		super(SamtoolsIndexWorkflow, self).__init__(args)
		self.schema["name"] = "samtools-index"
		self.output_bucket = args.output_bucket
		self.input_files = args.input_files

		if data_staging_script is None:
			self.data_staging_script_path = os.path.join(os.path.dirname(__file__), '/../scripts/samtools-index/data-staging.sh.template')
		else:
			self.data_staging_script_path = data_staging_script

		if samtools_index_script is None:
			self.samtools_index_script_path = os.path.join(os.path.dirname(__file__), '/../scripts/samtools-index/samtools-index.sh.template')
		else:
			self.samtools_index_script_path = samtools_index_script

		if cleanup_job_script is None:
			self.cleanup_job_script_path = os.path.join(os.path.dirname(__file__), '/../scripts/samtools-index/cleanup.sh.template')
		else:
			self.cleanup_script_path = cleanup_script

		self.data_staging_job_template = {
			"name": "stage-file-{filename}",
			"container_image": "google/cloud-sdk",
			"restart_policy": "OnFailure"
		}
		self.samtools_index_job_template = {
			"name": "samtools-index-{filename}",
			"container_image": "nasuno/samtools",
			"restart_policy": "OnFailure"
		}
		self.cleanup_job_template = {
			"name": "retrieve-index-{filename}",
			"container_image": "google/cloud-sdk",
			"restart_policy": "OnFailure"
		}

		self.__build()

	def __build(self):
		with open(self.input_files) as f:
			file_list = f.readlines()
		
		for url in file_list:
			try: 
				subprocess.check_call(["gsutil", "stat", url])
			except ValueError:
				print "There was a problem with url {url} in the input file".format(url=url)
			else:
				self.__create_subworkflow(url.strip())

	def __create_subworkflow(self, file_url):
		filename = file_url.split('/')[-1]
		if self.output_bucket is None:
			self.output_bucket = '/'.join(self.file_url.split('/')[0:-1])

		self.data_staging_job_template["name"].format(filename=filename.replace('.', '-').lower())
		self.data_staging_job_template["container_script"] = self.__load_script_template(self.data_staging_script_path, url=file_url, filename=filename)
	
		self.samtools_index_job_template["name"].format(filename=filename.replace('.', '-').lower())
		self.samtools_index_job_template["container_script"].self.__load_script_template(self.samtools_index_script_path, filename=filename)
		self.samtools_index_job_template["parents"] = [self.data_staging_job_template["name"]]
	
		self.cleanup_job_template["name"].format(filename=filename.replace('.', '-').lower())
		self.cleanup_job_template["container_script"] = self.__load_script_template(self.cleanup_script_path, filename=filename, destination=self.output_bucket)
		self.cleanup_job_template["parents"] = [self.samtools_index_job_template["name"]]

		self.schema["jobs"].extend([self.data_staging_job_template, self.samtools_index_job_template, self.cleanup_job_template])

class QcWorkflow(Workflow):
	def __init__(self, args, data_staging_script=None, qc_script=None, cleanup_script=None):
		super(QcWorkflow, self).__init__(args)
		self.schema["name"] = "fastqc-picard"
		self.input_files = args.input_files
		self.output_bucket = args.output_bucket

		if data_staging_script is None:
			self.data_staging_script_path = os.path.join(os.path.dirname(__file__), '/../scripts/qc/data-staging.sh.template')
		else:
			self.data_staging_script_path = data_staging_script

		if qc_script is None:
			self.qc_script_path = os.path.join(os.path.dirname(__file__), '/../scripts/qc/qc.sh.template')
		else:
			self.qc_script_path = qc_script

		if cleanup_job_script is None:
			self.cleanup_job_script_path = os.path.join(os.path.dirname(__file__), '/../scripts/qc/cleanup.sh.template')
		else:
			self.cleanup_script_path = cleanup_script

		self.data_staging_job_template = {
			"name": "stage-file-{filename}",
			"container_image": "google/cloud-sdk",
			"restart_policy": "OnFailure"
		}
		self.qc_job_template = {
			"name": "fastqc-{filename}",
			"container_image": "b.gcr.io/isb-cgc-public-docker-images/fastqc",
			"restart_policy": "OnFailure"
		}
		self.cleanup_job_template = {
			"name": "retrieve-stats-{filename}",
			"container_image": "google/cloud-sdk",
			"restart_policy": "OnFailure"
		}

		self.__build()
	
	def __build(self):
		with open(self.input_files) as f:
			file_list = f.readlines()
		
		for url in file_list:
			try: 
				subprocess.check_call(["gsutil", "stat", url])
			except ValueError:
				print "There was a problem with url {url} in the input file".format(url=url)
			else:
				self.__create_subworkflow(url.strip())
				

	def __create_subworkflow(self, url):
		filename = url.split('/')[-1]

		if self.output_bucket is None:
			self.output_bucket = '/'.join(url.split('/')[0:-1])

		self.data_staging_job_template["name"].format(filename=filename.replace('.', '-').lower())
		self.data_staging_job_template["container_script"] = self.__load_script_template(self.data_staging_script_path, url=url, filename=filename)
		self.qc_job_template["name"].format(filename=filename.replace('.', '-').lower())
		self.qc_job_template["container_script"] = self.__load_script_template(self.qc_script_path, filename=filename, basename='.'.join(filename.split('.')[0:-1]))
		self.qc_job_template["parents"] = [self.data_staging_job_template["name"]]
		self.cleanup_job_template["name"].format(filename=filename.replace('.', '-').lower())
		self.cleanup_job_template["container_script"] = self.__load_script_template(self.cleanup_script_path, filename=filename, basename='.'.join(filename.split('.')[0:-1]), destination=self.output_bucket)
		self.cleanup_job_template["parents"] = [self.qc_job_template["name"]]
		
		self.schema["jobs"].extend([self.data_staging_job_template, self.qc_job_template, self.cleanup_job_template])


def main(args):
	if args.workflow == "samtools-index":
		SamtoolsIndexWorkflow(args).run()
	elif args.workflow == "qc":
		FastQcWorkflow(args).run()

if __name__ == "__main__":
	# parse args -- project id, zone, node num, cluster node disk size, cluster nfs volume size, output bucket, list of gcs urls
	parser = argparse.ArgumentParser(description="ISB-CGC Compute Workflows")
	parser.add_argument('--project_id', required=True, help="GCP project id")
	parser.add_argument('--zone', required=True, help="GCE zone")
	parser.add_argument('--nodes', required=True, help="Number of nodes in the cluster")
	parser.add_argument('--cluster_node_disk_size', required=True, help="Cluster boot disk size in GB")
	parser.add_argument('--cluster_nfs_volume_size', required=True, help="NFS shared volume size in GB")
	parser.add_argument('--machine_type', required=True, help="GCE machine type")
	parser.add_argument('--no_tear_down', required=False, action='store_true', help="If set, the cluster won't be cleaned up at the end of the workflow.  Default is False")
	parser.add_argument('--dry_run', required=False, action='store_true', help="If set, will only print the workflow graph that would have run. Default is False")

	subparsers = parser.add_subparsers(help="sub-command help", dest="workflow")
	
	samtools_subparser = subparsers.add_parser('samtools-index', help="samtools-index workflow arguments")
	samtools_subparser.add_argument('--input_files', required=True, help="A plain text file containing a list of GCS URLs representing BAM files to index, one per line")
	samtools_subparser.add_argument('--output_bucket', required=False, default=None, help="The output bucket for the results files; if not provided, will default to the object hierarchy of the original input file")
	
	
	fastqc_subparser = subparsers.add_parser('qc', help="QC (fastqc + picard) workflow arguments")
	fastqc_subparser.add_argument('--input_files', required=True, help="A plain text file containing a list of GCS URLs representing fastq files (fastq, fastq.gz, fastq.tar, or tar.gz extensions) or BAM files, one per line")
	fastqc_subparser.add_argument('--output_bucket', required=False, help="The output bucket for the results files; if not provided, will default to the object hierarchy of the original input file")
	
	args = parser.parse_args()
	main(args)