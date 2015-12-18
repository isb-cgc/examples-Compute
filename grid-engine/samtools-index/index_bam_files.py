import re
import os
import json
import tempfile
import argparse
import cgc_gauth
import cgc_curl
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

def index_bam_files(file_list, storage, job_name, output_bucket, logs_bucket, grid_computing_tools_dir, copy_original_bam=False):
	# Create a text file containing the file list (one file per line)
	text_file_list = tempfile.mkstemp()
	config_file = tempfile.mkstemp()
	
	with open(text_file_list[0], 'w') as f:
		exit(0)
		for isb_cgc_bam_file in file_list:
			if copy_original_bam:
				# Update the path to the new location in the user's cloud storage space
				my_bam_file = bam_file.split('.')[-1]
				new_path = os.path.join(output_bucket, my_bam_file)

				# Copy the file to be indexed to the output bucket
				# Question 1: how do we get the bucket name for the files?
				# Question 2: which bucket contains the Percivall Pott TCGA cohort BAM files currently?
				try:
					response = storage.copy(sourceBucket="", sourceObject=isb_cgc_bam_file, destinationBucket=output_bucket, destinationObject=my_bam_file, body={}).execute()
				except: 
					# not sure what this will throw yet
					pass

				# Write the new file path to the file list
				f.write(new_path)
			else:
				f.write(isb_cgc_bam_file)
			
	# create the job config file
	with open(config_file[0], 'w') as g:
		g.write("export INPUT_LIST_FILE=%s" % text_file_list[1])
		g.write("export OUTPUT_PATH=%s" % output_bucket)
		g.write("export OUTPUT_LOG_PATH=%s" % logs_bucket)
		g.write("export SAMTOOLS_OPERATION=\"index\"")

	# submit the job
	output = subprocess.check_output(["%s/src/samtools/launch_samtools" % grid_computing_tools_dir, config_file[1]])
	print output

	if not copy_original_bams:
		copyfile(text_file_list[0], "%s-isb-cgc-bam-files.txt" % job_name)
		
	
def generate_file_list_from_sample(sample_barcode, auth_token):
	file_list = []
	endpoint = 'datafilenamekey_list'
	url = '/'.join( (api_root, api_name, api_ver, endpoint) )
	params = {
		"sample_barcode": sample_barcode,
		"token": auth_token
	}
	try:
		response = cgc_curl.get(url, params)
	except:
		print "There was a problem with the format of the request -- exiting"
		exit(-1)
	else:
		print response
		if len(response["datafilenamekeys"]) > 0:
			for datafilenamekey in response["datafilenamekeys"]:
				if datafilenamekey is not None and re.search(bam_pattern, datafilenamekey) is not None :
					file_list.append(datafilenamekey)
		else:
			print "No BAM files found for sample %s -- exiting" (sample_barcode)
			exit(0)
			
	return file_list

def generate_file_list_from_cohort(cohort_id, auth_token):
	file_list = []
	endpoint = 'cohort_patients_samples_list'
	url = '/'.join( (api_root, api_name, api_ver, endpoint) )
	params = {
		"cohort_id": str(cohort_id),
		"token": auth_token
	}

	try:
		response = cgc_curl.get(url, params)
	except:
		print "There was a problem with the format of the request -- exiting"
		exit (-1)
	else:
		print response
		if "samples" in response.keys() and len(response["samples"]) > 0:
			for barcode in response["samples"]:
				file_list.extend(generate_file_list_from_sample(barcode, auth_token))
		else:
			print "No BAM files found for cohort %s -- exiting" (cohort_id)
			exit(0)
			
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
	parser.add_argument('--copy_original_bam', required=False, 
		help='If set to True, will copy the original bam file from the ISB-CGC cloud storage space to the output bucket.  Otherwise a list of the original BAM locations in GCS will be generated in the current working directory.  Default: False')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--cohort_id', type=int, help='The cohort ID for which you\'d like to index associated BAM files.')
	group.add_argument('--sample_barcode', type=str, help='The sample barcode for which you\'d like to index associated BAM files.')
	
	args = parser.parse_args()
	
	# authenticate to ISB-CGC
	auth_object = cgc_gauth.get_credentials(oauth_flow_args=['--noauth_local_webserver']) # this is hacky... cgc_gauth.py may need some refactoring

	# create the cloud storage API object
	storage_credentials = GoogleCredentials.get_application_default()
	storage = build("storage", "v1", credentials=storage_credentials)
	
	# generate a list of files to index
	if "cohort_id" in args:
		file_list = generate_file_list_from_cohort(args.cohort_id, auth_object.access_token)
		
	elif "sample_barcode" in args:
		file_list = generate_file_list_from_sample(args.sample_barcode, auth_object.access_token)
	
	print file_list
	# run the indexing job
	index_bam_files(file_list, storage, args.job_name, args.output_bucket, args.log_bucket, args.grid_computing_tools_dir, args.copy_original_bam)

