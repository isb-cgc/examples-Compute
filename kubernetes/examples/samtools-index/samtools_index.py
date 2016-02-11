import sys
import pprint
import argparse
import subprocess
from KubernetesWorkflowRunner import KubernetesWorkflowRunner
from random import SystemRandom

def create_subworkflow(url, output_bucket):
	filename = url.split('/')[-1]
	data_staging_job_name = "stage-file-{filename}".format(filename=filename.replace('.', '-').lower())
	data_staging_job = {
		"container_image": "google/cloud-sdk",
		"container_script": """if [[ ! -a share/{filename} ]]; then gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp {url} share; else echo 'File {filename} already staged -- skipping'; fi""".format(url=url, filename=filename),
		"restart_policy": "OnFailure"
	}
	
	samtools_job_name = "samtools-index-{filename}".format(filename=filename.replace('.', '-').lower())	
	samtools_job = {
		"container_image": "nasuno/samtools",
		"container_script": """if [[ ! -a share/{filename}.success ]]; then cd scratch; cp ../share/{filename} .; samtools index {filename}; cp {filename}.bai ../share && touch ../share/{filename}.success; else echo 'File {filename} already indexed -- skipping'; fi""".format(filename=filename),
		"parents": [data_staging_job_name],
		"restart_policy": "OnFailure"
	}
	
	cleanup_job_name = "retrieve-index-{filename}".format(filename=filename.replace('.', '-').lower())
	cleanup_job = {
		"container_image": "google/cloud-sdk",
		"container_script": """if [[ -a share/{filename}.bai ]]; then gsutil -o Credentials:gs_oauth2_refresh_token=$(cat /data-access/refresh-token) -o Oauth2:oauth2_refresh_retries=50 cp share/{filename}.bai {destination}; else echo 'Index {filename}.bai not found'; fi""".format(filename=filename, destination=output_bucket),
		"parents": [samtools_job_name],
		"restart_policy": "OnFailure"
	}
	
	return [(data_staging_job_name, data_staging_job), (samtools_job_name, samtools_job), (cleanup_job_name, cleanup_job)]
	
def main(args):
	# set some variables
	samtools_index_schema = {
		"name": "samtools-index",
		"cluster": {
			"project_id": args.project_id,
			"zone": args.zone,
			"node_num": args.node_num,
			"network": "default",
			"machine_type": args.machine_type,
			"cluster_node_disk_size": args.cluster_node_disk_size,
			"cluster_nfs_volume_size": args.cluster_nfs_volume_size
		},
		"jobs": {}
	}
	# generate a Kubernetes workflow schema for the samtools index jobs
	with open(args.input_files) as f:
		file_list = f.readlines()
		
	for url in file_list:
		try: 
			subprocess.check_call(["gsutil", "stat", url])
		except ValueError:
			print "There was a problem with url {url} in the input file".format(url=url)
		else:
			subworkflow_jobs = create_subworkflow(url.strip(), args.output_bucket)
			for job_name, job in subworkflow_jobs:
				samtools_index_schema["jobs"][job_name] = job
	
	pprint.pprint(samtools_index_schema)
	workflow_runner = KubernetesWorkflowRunner(samtools_index_schema, "/tmp/samtools-index")
	output = workflow_runner.start()
	
if __name__ == "__main__":
	# parse args -- project id, zone, node num, cluster node disk size, cluster nfs volume size, output bucket, list of gcs urls
	parser = argparse.ArgumentParser(description="")
	parser.add_argument('--input_files', required=True, help="A plain text file containing a list of GCS URLs representing BAM files to index, one per line")
	parser.add_argument('--output_bucket', required=True, help="The output bucket for the BAM index files (BAI)")
	parser.add_argument('--project_id', required=True, help="")
	parser.add_argument('--zone', required=True, help="")
	parser.add_argument('--node_num', required=True, help="")
	parser.add_argument('--cluster_node_disk_size', required=True, help="")
	parser.add_argument('--cluster_nfs_volume_size', required=True, help="")
	parser.add_argument('--machine_type', required=True, help="")
	args = parser.parse_args()
	main(args)
