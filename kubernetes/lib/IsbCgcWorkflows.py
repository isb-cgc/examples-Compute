import os
import re
import sys
import math
import json
import pprint
import argparse
import subprocess
from KubernetesWorkflowRunner import KubernetesWorkflowRunner
from random import SystemRandom

DEFAULT_DATA_STAGING_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../scripts/data/data-staging.sh.template')
DEFAULT_CLEANUP_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../scripts/data/cleanup.sh.template')
DEFAULT_SAMTOOLS_INDEX_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../scripts/samtools-index/samtools-index.sh.template')
DEFAULT_QC_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), '../scripts/qc/qc.sh.template')

DATA_STAGING_JOB_TEMPLATE = {
	"container_image": "b.gcr.io/isb-cgc-public-docker-images/cloud-sdk-crcmod",
	"restart_policy": "OnFailure"
}

CLEANUP_JOB_TEMPLATE = {
	"container_image": "google/cloud-sdk",
	"restart_policy": "OnFailure",
	"cleanup": True
}

SAMTOOLS_INDEX_JOB_TEMPLATE = {
	"container_image": "nasuno/samtools",
	"restart_policy": "OnFailure"
}

QC_JOB_TEMPLATE = {
	"container_image": "b.gcr.io/isb-cgc-public-docker-images/qctools",
	"restart_policy": "OnFailure"
}

class WorkflowArguments(object):
	def __init__(self):
		super(WorkflowArguments, self).__init__()
		self.parser = argparse.ArgumentParser(description="ISB-CGC Computational Workflows")
		self.parser.add_argument('--project_id', required=True, help="GCP project id")
		self.parser.add_argument('--zone', required=True, help="GCE zone")
		self.parser.add_argument('--nodes', required=True, help="Number of nodes in the cluster")
		self.parser.add_argument('--cluster_node_disk_size', required=True, help="Cluster boot disk size in GB")
		self.parser.add_argument('--machine_type', required=True, help="GCE machine type")
		self.parser.add_argument('--tear_down', required=False, action='store_true', help="If set, the cluster will be cleaned up at the end of the workflow.  Default is False")
		self.parser.add_argument('--dry_run', required=False, action='store_true', help="If set, will only print the workflow graph that would have run. Default is False")
		self.parser.add_argument('--add_secret', required=False, default=None, action='append', help="An additional secret to add to the cluster, formatted as a comma-delimited string: <secret-name>,<secret-gcs-url>,<secret-mount-path>")
		self.parser.add_argument('--shared_file', required=False, default=None, action='append', help="A shared file to be used among multiple subworkflows.  Must be a valid GCS url.")

		subparsers = self.parser.add_subparsers(help="sub-command help", dest="workflow")
	
		samtools_subparser = subparsers.add_parser('samtools-index', help="samtools-index workflow arguments")
		samtools_subparser.add_argument('--input_files', required=True, help="A plain text file containing a list of GCS URLs representing BAM files to index, one per line")
		samtools_subparser.add_argument('--output_bucket', required=False, default=None, help="The output bucket for the results files; if not provided, will default to the object hierarchy of the original input file")
	
		fastqc_subparser = subparsers.add_parser('qc', help="QC (fastqc + picard) workflow arguments")
		fastqc_subparser.add_argument('--input_files', required=True, help="A plain text file containing a list of GCS URLs representing fastq files (fastq, fastq.gz, fastq.tar, or tar.gz extensions) or BAM files, one per line")
		fastqc_subparser.add_argument('--output_bucket', required=False, help="The output bucket for the results files; if not provided, will default to the object hierarchy of the original input file")

class WorkflowStep(object):
	def __init__(self, template, name, container_script, **kwargs):
		self.template = template.copy()
		self.template["name"] = name
		self.template["container_script"] = self.load_script_template(container_script, **kwargs)
		
	def link_child(self, step):
		if "parents" in step.template.keys():
			step.template["parents"].append(self.template["name"])
		else:
			step.template["parents"] = [self.template["name"]]
		
	def load_script_template(self, path, **params):
		script_lines = []
		with open(path) as f:
			for line in f:
				script_lines.append(line.strip())

		return ';'.join(script_lines).format(**params)
		
		
class Workflow(object):
	def __init__(self, cluster):
		self.dry_run = cluster.dry_run
		self.schema = {
			"name": None,
			"cluster": {
				"project_id": cluster.project_id,
				"zone": cluster.zone,
				"nodes": cluster.nodes,
				"network": "default",
				"machine_type": cluster.machine_type,
				"cluster_node_disk_size": cluster.cluster_node_disk_size,
				"tear_down": cluster.tear_down,
				"secrets": [],
				"shared_files": []
			},
			"jobs": []
		}
		if cluster.add_secret is not None:
			for secret in cluster.add_secret:
				secret_details = secret.split(',')
				secret_spec = {
					"name": secret_details[0],
					"url": secret_details[1],
					"mount_path": secret_details[2]
				}
				self.schema["cluster"]["secrets"].append(secret_spec)

	def __build(self):
		pass # to be "overridden" in subclasses

	def create_subworkflow(self, steps, subworkflow_name, host_key=None):
		i = 0
		j = 1
		jobs_list = []
		while i < len(steps):
			steps[i].template["subworkflow_name"] = subworkflow_name
			steps[i].template["host_key"] = host_key
			if j < len(steps):
				steps[i].link_child(steps[j])

			jobs_list.append(steps[i].template)
			i += 1
			j += 1
		
		self.schema["jobs"].extend(jobs_list)
		
	@staticmethod
	def createDefaultDataStagingStep(filename, analysis_id, url):
		return WorkflowStep(DATA_STAGING_JOB_TEMPLATE, "stage-file-{analysis_id}".format(analysis_id=analysis_id), DEFAULT_DATA_STAGING_SCRIPT_PATH, url=url, filename=filename)
		
	@staticmethod
	def createDefaultCleanupStep(filename, analysis_id, destination):
		return WorkflowStep(CLEANUP_JOB_TEMPLATE, "retrieve-index-{analysis_id}".format(analysis_id=analysis_id), DEFAULT_CLEANUP_SCRIPT_PATH, filename=filename, destination=destination)

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
			self.data_staging_script_path = DEFAULT_DATA_STAGING_SCRIPT_PATH
		else:
			self.data_staging_script_path = data_staging_script

		if samtools_index_script is None:
			self.samtools_index_script_path = DEFAULT_SAMTOOLS_INDEX_SCRIPT_PATH
		else:
			self.samtools_index_script_path = samtools_index_script

		if cleanup_job_script is None:
			self.cleanup_script_path = DEFAULT_CLEANUP_SCRIPT_PATH
		else:
			self.cleanup_script_path = cleanup_script

		self.__build()

	def __build(self):
		with open(self.input_files) as f:
			file_list = f.readlines()
			
		total_hosts = int(self.schema["cluster"]["nodes"])
		host_key = 0
		
		for url in file_list:
			if host_key >= total_hosts:
				host_key = host_key % total_hosts
				
			url = url.strip()
			try:
				metadata = subprocess.check_output(['gsutil', 'ls', '-L', '{url}'.format(url=url)])
			except subprocess.CalledProcessError as e:
				print "URL {url} doesn't exist".format(url=url)
				exit(-1)
			else:

				metadata_tag = metadata.partition('Metadata:')[2].partition('Hash')[0]
				analysis_id = metadata_tag.strip().split()[-1]
				filename = url.split('/')[-1]
				subworkflow_name = "samtools-index-{analysis_id}".format(analysis_id=analysis_id)
				
				if self.output_bucket is None:
					self.output_bucket = '/'.join(self.url.split('/')[0:-1])
					
				data_staging_step = self.createDefaultDataStagingStep(filename, analysis_id, url)
				samtools_index_step = self.createDefaultSamtoolsIndexStep(filename, analysis_id)
				cleanup_step = self.createDefaultCleanupStep(filename, analysis_id, self.output_bucket)

				self.create_subworkflow([ data_staging_step, samtools_index_step, cleanup_step ], subworkflow_name, host_key)
				host_key += 1
	
	@staticmethod
	def createDefaultSamtoolsIndexStep(filename, analysis_id):
		return WorkflowStep(SAMTOOLS_INDEX_JOB_TEMPLATE, "samtools-index-{analysis_id}".format(analysis_id=analysis_id), DEFAULT_SAMTOOLS_INDEX_SCRIPT_PATH, filename=filename)

class QcWorkflow(Workflow):
	def __init__(self, args, data_staging_script=None, qc_script=None, cleanup_script=None):
		super(QcWorkflow, self).__init__(args)
		self.schema["name"] = "fastqc-picard"
		self.input_files = args.input_files
		self.output_bucket = args.output_bucket

		if data_staging_script is None:
			self.data_staging_script_path = DEFAULT_DATA_STAGING_SCRIPT_PATH
		else:
			self.data_staging_script_path = data_staging_script

		if qc_script is None:
			self.qc_script_path = DEFAULT_QC_SCRIPT_PATH
		else:
			self.qc_script_path = qc_script

		if cleanup_script is None:
			self.cleanup_script_path = DEFAULT_CLEANUP_SCRIPT_PATH
		else:
			self.cleanup_script_path = cleanup_script


		self.__build()
	
	def __build(self):
		with open(self.input_files) as f:
			file_list = f.readlines()
		
		total_hosts = int(self.schema["cluster"]["nodes"])
		host_key = 0

		for url in file_list:
			if host_key >= total_hosts:
				host_key = host_key % total_hosts

			url = url.strip()
			
			try:
				metadata = subprocess.check_output(['gsutil', 'ls', '-L', '{url}'.format(url=url)])
			except subprocess.CalledProcessError as e:
				print "URL {url} doesn't exist".format(url=url)
				exit(-1)
			else:
				metadata_tag = metadata.partition('Metadata:')[2].partition('Hash')[0]
				analysis_id = metadata_tag.strip().split()[-1]
				filename = url.split('/')[-1]
				subworkflow_name = "qc-{filename}".format(filename=filename)

				if self.output_bucket is None:
					self.output_bucket = '/'.join(url.split('/')[0:-1])
					
				data_staging_step = self.createDefaultDataStagingStep(filename, analysis_id, url)
				qc_step = self.createDefaultQcStep(filename, analysis_id)
				cleanup_step = self.createDefaultCleanupStep(filename, analysis_id, self.output_bucket)
				cleanup_bai = self.createDefaultCleanupStep("{filename}.bai".format(filename=filename), analysis_id, '/'.join(url.split('/')[0:-1]))
				self.create_subworkflow([ data_staging_step, qc_step, cleanup_step, cleanup_bai ], subworkflow_name, host_key)
				host_key += 1
	
	@staticmethod		
	def createDefaultQcStep(filename, analysis_id):
		return WorkflowStep(QC_JOB_TEMPLATE, "fastqc-{analysis_id}".format(analysis_id=analysis_id), DEFAULT_QC_SCRIPT_PATH, filename=filename)


def main(args):
	if args.workflow == "samtools-index":
		SamtoolsIndexWorkflow(args).run()
	elif args.workflow == "qc":
		QcWorkflow(args).run()

if __name__ == "__main__":
	parser = WorkflowArguments().parser
	args = parser.parse_args()
	main(args)
