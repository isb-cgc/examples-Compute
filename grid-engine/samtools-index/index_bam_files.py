import re
import os
import json
import tempfile
import argparse
import httplib2
import isb_auth, isb_curl
import requests
import subprocess
from shutil import copyfile
from urllib import urlencode
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

# This script will find all BAM files associated with a given cohort or sample, then copy those BAM files to the user's cloud storage space for indexing.

def index_bam_files(file_list, storage, job_name, output_bucket, logs_bucket, grid_computing_tools_dir, copy_original_bams, dry_run):
	# Create a text file containing the file list (one file per line)
	if not os.path.exists("{home}/samtools-index-config".format(home=os.environ['HOME'])):
		os.makedirs("{home}/samtools-index-config".format(home=os.environ['HOME']))

	text_file_list = tempfile.NamedTemporaryFile(dir="{home}/samtools-index-config".format(home=os.environ['HOME']), delete=False)
	config_file = tempfile.NamedTemporaryFile(dir="{home}/samtools-index-config".format(home=os.environ['HOME']), delete=False)
	
	with open(text_file_list.name, 'w') as f:
		for isb_cgc_bam_file in file_list:
			if copy_original_bams:
				# Update the path to the new location in the user's cloud storage space
				my_bam_file = isb_cgc_bam_file.split('/')[-1]
				new_path = os.path.join(output_bucket, my_bam_file)

				# Get the source bucket name and object
				source = isb_cgc_bam_file.split('/')
				source_bucket = source[2]
				source_object = '/'.join(source[3:])

				# Get the destination bucket name
				destination = new_path.split('/')
				destination_bucket = destination[2]

				# Copy the file to be indexed to the output bucket
				if dry_run:
					print "would have copied source bucket %s, source object %s, to destination bucket %s, destination object %s"
				else:
					try:
						storage.objects().copy(sourceBucket=source_bucket, sourceObject=source_object, destinationBucket=destination_bucket, destinationObject=my_bam_file, body={}).execute()				
					except: 
						# not sure what this will throw yet
						print "couldn't copy bam file from isb-cgc to personal cloud storage!"
						exit(-1)

				# Write the new file path to the file list
				f.write("{new_path}\n".format(new_path=new_path))
			else:
				f.write("{isb_cgc_bam_file}\n".format(isb_cgc_bam_file=isb_cgc_bam_file))
			
	# create the job config file
	with open(config_file.name, 'w') as g:
		g.write("export INPUT_LIST_FILE=%s\n" % text_file_list.name)
		g.write("export OUTPUT_PATH=%s\n" % output_bucket)
		g.write("export OUTPUT_LOG_PATH=%s\n" % logs_bucket)
		g.write("export SAMTOOLS_OPERATION=\"index\"")

	if dry_run:
		print "would've run {grid_computing_tools_dir}/src/samtools/launch_samtools.sh {config}".format(grid_computing_tools_dir=grid_computing_tools_dir, config=config_file.name)
	else:
		# submit the job
		output = subprocess.check_output(["{grid_computing_tools_dir}/src/samtools/launch_samtools.sh".format(grid_computing_tools_dir=grid_computing_tools_dir), "{config}".format(config=config_file.name)])

	if not copy_original_bams:
		copyfile(text_file_list.name, "%s-isb-cgc-bam-files.txt" % job_name)
		
	
def generate_file_list(url, headers):
	bam_pattern = '^.*\.bam$'
	file_list = []
	response = requests.get(url, headers)
	print response.json()
	print response.content
	if response.json()["count"] > 0:
		for datafilenamekey in response["datafilenamekeys"]:
			if re.search(bam_pattern, datafilenamekey) is not None :
				file_list.append(datafilenamekey)
	else:
		print "No BAM files found"
			
	return file_list

if __name__ == "__main__":
	# parse args
	parser = argparse.ArgumentParser(description='Index ISB-CGC BAM files by cohort or sample')
	parser.add_argument('--job_name', required=True, 
		help='A name for this job.')
	parser.add_argument('--output_bucket', required=True, 
		help='The destination bucket for all outputs.  Must be a valid Google Cloud Storage bucket URL, i.e. gs://bucket_name. Required')
	parser.add_argument('--logs_bucket', required=True, 
		help='The destination bucket for all logs.  Must be a valid Google Cloud Storage bucket URL, i.e. gs://bucket_name. Required')
	parser.add_argument('--grid_computing_tools_dir', required=True,
		help='Path to the root directory of the "grid-computing-tools" repository. Required')
	group1 = parser.add_mutually_exclusive_group(required=True)
	group1.add_argument('--cohort_id', type=int, help='The cohort ID for which you\'d like to index associated BAM files.')
	group1.add_argument('--sample_barcode', type=str, help='The sample barcode for which you\'d like to index associated BAM files.')
	group1.add_argument('--gcs_dir_url', type=str, help='A URL to a directory in GCS to copy files from (rather than going through the API)')
	group2 = parser.add_mutually_exclusive_group(required=True)
	group2.add_argument('--copy_original_bams', action='store_true', default=False,
		help='If set, will copy the original bam files from the ISB-CGC cloud storage space to the output bucket.  Otherwise a list of the original BAM locations in GCS will be generated in the current working directory.  Default: False')
	group2.add_argument('--dry_run', action='store_true', default=False,
		help='If set, will not copy or index any BAM files, but will display the copy and index operations that would have occurred during a real run. Default: False')
	
	args = parser.parse_args()
	
	# authenticate to ISB-CGC
	#credentials = isb_auth.get_credentials()
	credentials = GoogleCredentials.get_application_default()
	credentials.authorize(httplib2.Http())
	if credentials.access_token_expired:
		credentials.refresh(httplib2.Http())

	# create the cloud storage and isb API objects
	storage = build("storage", "v1", http=credentials.authorize(httplib2.Http()))
	
	# generate a list of files to index
	url = 'https://mvm-dot-isb-cgc.appspot.com/_ah/api/cohort_api/v1/alt_datafilenamekey_list/?{query_param}={query_param_value}'  #TODO: Update this with the production URL
	headers = {
		"Authorization": "Bearer {token}".format(token=credentials.access_token)
	}
	print args
	if args.cohort_id is not None:
		url.format(query_param="cohort_id", query_param_value=args.cohort_id)
		file_list = generate_file_list(url, headers)
	elif args.sample_barcode is not None:
		url.format(query_param="sample_barcode", query_param_value=args.sample_barcode)
		file_list = generate_file_list(url, headers)
	elif args.gcs_dir_url is not None:
		bucket = args.gcs_dir_url.split('/')[2]
		prefix = '/'.join(args.gcs_dir_url.split('/')[3:])
		items_list = storage.objects().list(bucket=bucket, prefix=prefix).execute()["items"]
		file_list = []
		for item in items_list:
			file_list.append("gs://{bucket}/{item}".format(bucket=bucket, item=item["name"]))
	
	if len(file_list) > 0:
		# run the indexing job
		index_bam_files(file_list, storage, args.job_name, args.output_bucket, args.logs_bucket, args.grid_computing_tools_dir, args.copy_original_bams, args.dry_run)


