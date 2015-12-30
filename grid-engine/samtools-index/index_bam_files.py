import re
import os
import json
import tempfile
import argparse
import isb_auth
import isb_curl
import subprocess
from shutil import copyfile
from urllib import urlencode
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

# This script will find all BAM files associated with a given cohort or sample, then copy those BAM files to the user's cloud storage space for indexing.

api_root = 'https://mvm-dot-isb-cgc.appspot.com/_ah/api'  #TODO: Update this with the production URL
api_name = 'cohort_api'
api_ver = 'v1';
bam_pattern = '^.*\.bam$'
endpoint = "datafilenamekey_list"

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
		
	
def generate_file_list(url, params):
	file_list = []
	try:
		response = isb_curl.get(url, params)
	except:
		print "There was a problem with the format of the request -- exiting"
		exit(-1)
	else:
		if response["count"] > 0:
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
	group2 = parser.add_mutually_exclusive_group(required=True)
	group2.add_argument('--copy_original_bams', action='store_true', default=False,
		help='If set, will copy the original bam files from the ISB-CGC cloud storage space to the output bucket.  Otherwise a list of the original BAM locations in GCS will be generated in the current working directory.  Default: False')
	group2.add_argument('--dry_run', action='store_true', default=False,
		help='If set, will not copy or index any BAM files, but will display the copy and index operations that would have occurred during a real run. Default: False')
	
	args = parser.parse_args()
	
	# authenticate to ISB-CGC
	auth_object = isb_auth.get_credentials()

	# create the cloud storage API object
	storage_credentials = GoogleCredentials.get_application_default()
	storage = build("storage", "v1", credentials=storage_credentials)
	
	# generate a list of files to index
	url = '/'.join( (api_root, api_name, api_ver, endpoint) )
	if "cohort_id" in args:
		params = {
			"cohort_id": str(args.cohort_id),
		}
		file_list = generate_file_list(url, params)
		
	elif "sample_barcode" in args:
		params = {
			"sample_barcode": sample_barcode,
		}
		file_list = generate_file_list(url, params)
	
	if len(file_list) > 0:
		# run the indexing job
		index_bam_files(file_list, storage, args.job_name, args.output_bucket, args.logs_bucket, args.grid_computing_tools_dir, args.copy_original_bams, args.dry_run)


