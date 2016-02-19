import re
import sys
import json
import pprint
import argparse
import subprocess
from KubernetesWorkflowRunner import KubernetesWorkflowRunner
from random import SystemRandom

class Workflow(object):
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

	def __build(self):
		pass # to be overridden in subclasses

	def __create_subworkflow(self):
		pass # to be overridden in subclasses

	def run(self):
		pprint.pprint(self.schema)
		KubernetesWorkflowRunner(self.schema, "/tmp/{workflow}".format(workflow=self.schema["name"])).start()

class SamtoolsIndexWorkflow(Workflow):
	def __init__(self, args):
		super(SamtoolsIndexWorkflow, self).__init__(args)
		self.schema["name"] = "samtools-index"
		self.output_bucket = args.output_bucket
		self.input_files = args.input_files

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

		data_staging_job = {
			"name": "stage-file-{filename}".format(filename=filename.replace('.', '-').lower()),
			"container_image": "google/cloud-sdk",
			"container_script": """if [ ! -f share/{filename} ]; then gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp {url} share; else echo 'File {filename} already staged -- skipping'; fi""".format(url=file_url, filename=filename),
			"restart_policy": "OnFailure"
		}
	
		samtools_job = {
			"name": "samtools-index-{filename}".format(filename=filename.replace('.', '-').lower()),
			"container_image": "nasuno/samtools",
			"container_script": """if [ ! -f share/{filename}.success ]; then cd scratch; cp ../share/{filename} .; samtools index {filename}; cp {filename}.bai ../share && touch ../share/{filename}.success && rm ../share/{filename}; else echo 'File {filename} already indexed -- skipping'; fi""".format(filename=filename),
			"parents": [data_staging_job["name"]],
			"restart_policy": "OnFailure"
		}
	
		cleanup_job = {
			"name": "retrieve-index-{filename}".format(filename=filename.replace('.', '-').lower()),
			"container_image": "google/cloud-sdk",
			"container_script": """if [ -f share/{filename}.bai ]; then gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp share/{filename}.bai {destination}; else echo 'Index {filename}.bai not found'; fi""".format(filename=filename, destination=self.output_bucket),
			"parents": [samtools_job["name"]],
			"restart_policy": "OnFailure"
		}
	
		self.schema["jobs"].extend([data_staging_job, samtools_job, cleanup_job])

class FastQcWorkflow(Workflow):
	def __init__(self, args):
		super(FastQcWorkflow, self).__init__(args)
		self.schema["name"] = "fastqc"
		self.input_files = args.input_files
		self.output_bucket = args.output_bucket
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
		bam_pattern = "^.*\.bam$"
		fastq_tar_pattern = "^.*\.fastq.tar$"
		tar_gz_pattern = "^.*\.tar.gz$"

		if self.output_bucket is None:
			self.output_bucket = '/'.join(url.split('/')[0:-1])

		data_staging_job = {
			"name": "stage-file-{filename}".format(filename=filename.replace('.', '-').lower()),
			"container_image": "google/cloud-sdk",
			"container_script": """if [ ! -f share/{filename} ]; then gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp {url} share; else echo 'File {filename} already staged -- skipping'; fi""".format(url=url, filename=filename),
			"restart_policy": "OnFailure"
		}

		tar_job = {
			"name": "extract-file-{filename}".format(filename=filename.replace('.', '-').lower()),
			"container_image": "ubuntu",
			"container_script": """if [ ! -f share/{filename}.contents ]]; then tar -xfvt share/{filename} > share/{filename}.contents; fi""".format(filename=filename),
			"parents": [data_staging_job["name"]],
			"restart_policy": "Never"
		}

		fastqc_job = {
			"name": "fastqc-{filename}".format(filename=filename.replace('.', '-').lower()),
			"container_image": "b.gcr.io/isb-cgc-public-docker-images/fastqc",
			"container_script": """if [ ! -f share/{filename}.success ]; then if [ -f share/{filename}.contents ]; then cd scratch; cp ../share/{filename}* .; cat {filename}.contents | tr '\n' | xargs -0 -n1 fastqc; else cd scratch; cp ../share/{filename} .; fastqc {filename}; fi; ls -al; cp {filename}*_fastqc.zip {filename}*_fastqc.html ../share && touch ../share/{filename}.success && rm ../share/{filename}; else echo 'File {filename} already processed -- skipping'; fi""".format(filename='.'.join(filename.split('.')[0:-1])),
			"parents": [],
			"restart_policy": "OnFailure"
		}
		
		if re.match(fastq_tar_pattern, filename) or re.match(tar_gz_pattern, filename):
			fastqc_job["parents"].append(tar_job["name"])
			self.schema["jobs"].append(tar_job)
		else:
			fastqc_job["parents"].append(data_staging_job["name"])
	
		cleanup_job = {
			"name": "retrieve-stats-{filename}".format(filename=filename.replace('.', '-').lower()),
			"container_image": "google/cloud-sdk",
			"container_script": """if [ -f share/{filename}.success ]; then gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp share/{filename}* {destination}; else echo 'Success indicator file not found'; fi""".format(filename=filename, destination=self.output_bucket),
			"parents": [fastqc_job["name"]],
			"restart_policy": "OnFailure"
		}
	
		self.schema["jobs"].extend([data_staging_job, fastqc_job, cleanup_job])

def main(args):
	if args.workflow == "samtools-index":
		SamtoolsIndexWorkflow(args).run()
	elif args.workflow == "fastqc":
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

	subparsers = parser.add_subparsers(help="sub-command help", dest="workflow")
	
	samtools_subparser = subparsers.add_parser('samtools-index', help="samtools-index workflow arguments")
	samtools_subparser.add_argument('--input_files', required=True, help="A plain text file containing a list of GCS URLs representing BAM files to index, one per line")
	samtools_subparser.add_argument('--output_bucket', required=False, default=None, help="The output bucket for the results files; if not provided, will default to the object hierarchy of the original input file")
	
	
	fastqc_subparser = subparsers.add_parser('fastqc', help="fastq workflow arguments")
	fastqc_subparser.add_argument('--input_files', required=True, help="A plain text file containing a list of GCS URLs representing fastq files (fastq, fastq.gz, fastq.tar, or tar.gz extensions), one per line")
	fastqc_subparser.add_argument('--output_bucket', required=False, help="The output bucket for the results files; if not provided, will default to the object hierarchy of the original input file")
	
	args = parser.parse_args()
	main(args)
