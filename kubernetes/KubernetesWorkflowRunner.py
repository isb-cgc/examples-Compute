import re
import sys
import json
import random
import pprint
import colander
import httplib2
import argparse
import subprocess
from copy import deepcopy
from KubernetesToilJobs import *
#from KubernetesWorkflowSchema import *
from toil.job import Job, JobGraphDeadlockException

class KubernetesWorkflowRunner():
	def __init__(self, workflow_spec, job_store):
		self.workflow_spec = workflow_spec
		self.workflow_name = workflow_spec["name"]
		self.job_store = job_store
		self.toil_jobs = {}

		# schema validation
		self._validate_schema()
		
		# assemble the workflow
		self._construct_kubernetes_toil_workflow()

		# graph (DAG) validation
		try:
			self.toil_jobs[self.workflow_name].checkJobGraphAcylic() # should be "checkJobGraphAcyclic" -- this is a real typo in the API!
		except JobGraphDeadlockException as e:
			exit(-1)

		try: 
			self.toil_jobs[self.workflow_name].checkJobGraphConnected()
		except JobGraphDeadlockException as e:
			exit(-1)
		
	def _construct_kubernetes_toil_workflow(self):
		# create a root job which will be the parent of all jobs beneath it
		#workflow_object = self.workflow_spec[self.workflow_name]
		cluster_config = self.workflow_spec["cluster"]
		
		args =  [ self.workflow_name, cluster_config["project_id"], cluster_config["zone"], cluster_config["node_num"], cluster_config["machine_type"], cluster_config["cluster_node_disk_size"], cluster_config["cluster_nfs_volume_size"] ]

		kwargs = {}
		if "logging_service" in cluster_config.keys():
			kwargs.update({"logging_service": cluster_config["logging_service"]})
	
		if "monitoring_service" in cluster_config.keys():
			kwargs.update({"monitoring_service": cluster_config["monitoring_service"]})

		if "tear_down" in cluster_config.keys():
			kwargs.update({"tear_down": cluster_config["tear_down"]})
	
		self.toil_jobs[self.workflow_name] = KubernetesToilWorkflow(*args, **kwargs)
	
		# first create all of the root jobs
		child_jobs = []
		for job in self.workflow_spec["jobs"]:
			if "parents" not in job.keys() or job["parents"] is None or len(job["parents"]) == 0:
				self._add_kubernetes_toil_job(self.toil_jobs[self.workflow_name], job["name"], job_object)
			else:
				child_jobs.append(job["name"])
	
		# add the child jobs (iteratively)
		def find_job(job_name):
			for job in self.toil_jobs:
				if job["name"] == job_name:
					return job

		while len(child_jobs) > 0:
			job_name = child_jobs.pop(0)
			parents_not_found = 0
			job = find_job(job_name)
			for parent in job["parents"]:
				if parent not in self.toil_jobs.keys():
					parents_not_found += 1

			if parents_not_found == 0:
				for parent in job["parents"]:
					self._add_kubernetes_toil_job(self.toil_jobs[parent], job_name, job)

			else:
				child_jobs.append(job_name)

	def _add_kubernetes_toil_job(self, parent, job_name, job_object):
		if job_name not in self.toil_jobs.keys():
			# create a new job as long as this job doesn't exist yet
			args = [ self.workflow_name, job_name, job_object["container_image"], job_object["container_script"] ]
			kwargs = {}
			if "restart_policy" in job_object.keys():
				kwargs.update({"restart_policy": job_object["restart_policy"]})
				
			self.toil_jobs[job_name] = KubernetesToilComputeJob(*args, **kwargs)

		if not parent.hasChild(self.toil_jobs[job_name]):
			parent.addChild(self.toil_jobs[job_name])

	def _validate_schema(self): 
		try:
			jobs_list = self.workflow_spec["jobs"]
		except KeyError as e:
			print "There was a problem getting the list of jobs from the workflow spec: {reason}".format(reason=e)
			exit(-1)
		else:
			try:
				workflow = Workflow(jobs_list=jobs_list)
			except:
				exit(-1)
			else:
				try: 
					workflow.deserialize(self.workflow_spec)
				except colander.Invalid as e:
					print "Couldn't validate the workflow schema: {reason}".format(reason=e)
					exit(-1)

	def start(self):
		options = Job.Runner.getDefaultOptions(self.job_store)
		Job.Runner.startToil(self.toil_jobs[self.workflow_name], options)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='')
	parser.add_argument('workflow_spec', help='The path to the JSON formatted workflow specification file')
	Job.Runner.addToilOptions(parser)
	
	args = parser.parse_args()

	# input validation
	try:
		with open(args.workflow_spec) as workflow_spec_fh:
			workflow_spec = json.load(workflow_spec_fh)
	except IOError as e:
		# do some error handling ... will also need to handle JSON related exceptions as well.
		print "There was a problem with the workflow specification file."
		exit(-1)

	workflow_runner = KubernetesWorkflowRunner(workflow_spec, args.jobStore)
	workflow_runner.start()




