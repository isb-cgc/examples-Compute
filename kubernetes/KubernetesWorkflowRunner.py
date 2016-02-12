import re
import sys
import json
import random
import pprint
import httplib2
import argparse
import subprocess
from copy import deepcopy
from KubernetesToilJobs import *
from jsonspec.validators import load #jsonspec is licensed under BSD
from jsonspec.reference import resolve
from toil.job import Job, JobGraphDeadlockException

class KubernetesWorkflowRunner():
	def __init__(self, workflow_spec, job_store):
		self.workflow_spec = workflow_spec
		self.workflow_name = self.workflow_spec["name"]
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
			if "parents" not in job.keys() or len(job["parents"]) == 0:
				self._add_kubernetes_toil_job(self.toil_jobs[self.workflow_name], job)
			else:
				child_jobs.append(job)
	
		# add the child jobs (iteratively)
		while len(child_jobs) > 0:
			job = child_jobs.pop(0)
			parents_not_found = 0
			
			for parent in job["parents"]:
				if parent not in self.toil_jobs.keys():
					parents_not_found += 1

			if parents_not_found == 0:
				for parent in job["parents"]:
					self._add_kubernetes_toil_job(self.toil_jobs[parent], job)

			else:
				child_jobs.append(job)

	def _add_kubernetes_toil_job(self, parent, job):
		if job["name"] not in self.toil_jobs.keys():
			# create a new job as long as this job doesn't exist yet
			args = [ self.workflow_name, job["name"], job["container_image"], job["container_script"] ]
			kwargs = {}
			if "restart_policy" in job.keys():
				kwargs.update({"restart_policy": job["restart_policy"]})
				
			self.toil_jobs[job["name"]] = KubernetesToilComputeJob(*args, **kwargs)

		if not parent.hasChild(self.toil_jobs[job["name"]]):
			parent.addChild(self.toil_jobs[job["name"]])

	def _validate_schema(self): 
		try:
			jobs = self.workflow_spec["jobs"]
		except KeyError as e:
			print "There was a problem getting the list of jobs from the workflow specification"
			exit(-1)

		job_names = []
		for job in jobs:
			job_names.append(job["name"])
	
		if len(job_names) != len(set(job_names)):
			print "Job names must be unique"
			exit(-1)
			
		for job in jobs:
			if "parents" in job.keys():
				for parent in job["parents"]:
					if parent not in job_names:
						print "Job '{job_name}' specifies a parent that doesn't exist".format(job_name=job["name"])
						exit(-1)

		workflow_schema = {
			"description": "Kubernetes Workflow Graph Schema",
			"type": "object",
			"additionalProperties": { "$ref": "#/definitions/workflow" },
			"definitions": {
				"workflow": {
					"name": {
						"description": "The name of the workflow",
						"type": "string",
						"required": True
					},
					"cluster": {
						"description": "Kubernetes cluster configuration",
						"type": "object",
						"properties": { "$ref": "#/definitions/cluster_properties" },
						"required": True
					},
					"jobs": {
						"description": "Container jobs to run on the cluster",
						"type": "array",
						"items": {
							"type": "object"
						},
						"properties": { "$ref": "#/definitions/job_properties" },
						"required": True
					}
				},
				"cluster_properties": {
					"project_id": {
						"type": "string",
						"required": True
					},
					"zone": {
						"type": "string",
						"required": True
					},
					"nodes": {
						"type": "int",
						"required": True
					},
					"network": {
						"type": "string",
						"required": False
					},
					"machine_type": {
						"type": "string",
						"required": True
					},
					"cluster_node_disk_size": {
						"type": "int",
						"required": True

					},
					"cluster_nfs_volume_size": {
						"type": "string",
						"required": True
					},
					"logging_service": {
						"type": "string",
						"required": False
				
					},
					"monitoring_service": {
						"type": "string",
						"required": False
					}
				},
				"job_properties": {
					"name": {
						"type": "string",
						"required": True
					},
					"container_image": {
						"type": "string",
						"required": True
					},
					"container_script": {
						"type": "string",
						"required": True
					},
					"parents": {
						"type": "array", 
						"items": {
							"type": "string",
							"oneOf": job_names
						},
						"required": False
					}, 
					"restart_policy": {
						"type": "string",
						"oneOf": ["OnFailure", "Always", "Never"],
						"required": False
					}
				}
			}
		}

		validator = load(workflow_schema)
		validator.validate(self.workflow_spec)
		try:
			validator.validate(self.workflow_spec)
		except: # what kind of exception?
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




