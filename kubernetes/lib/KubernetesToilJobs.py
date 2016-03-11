import os
import pwd
import json
import time
import base64
import string
import requests
import datetime
import httplib2
import subprocess
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from googleapiclient.errors import HttpError
from toil.job import Job
from random import randint, SystemRandom

# Kubernetes API URIs
API_ROOT = "http://localhost:8080"
NAMESPACE_URI = "/api/v1/namespaces/"
PODS_URI = "/api/v1/namespaces/{namespace}/pods/"
SERVICES_URI = "/api/v1/namespaces/{namespace}/services/"
REPLICATION_CONTROLLERS_URI = "/api/v1/namespaces/{namespace}/replicationcontrollers/"
PERSISTENT_VOLUMES_URI = "/api/v1/persistentvolumes/" 
PERSISTENT_VOLUME_CLAIMS_URI = "/api/v1/namespaces/{namespace}/persistentvolumeclaims/" 
SECRETS_URI = "/api/v1/namespaces/{namespace}/secrets/"

# Configuration
CREDENTIALS = GoogleCredentials.get_application_default()
HTTP=CREDENTIALS.authorize(httplib2.Http())
if CREDENTIALS.access_token_expired:
	CREDENTIALS.refresh(HTTP)
	
GKE = discovery.build('container', 'v1', http=HTTP)
COMPUTE = discovery.build('compute', 'v1', http=HTTP)
SESSION = requests.Session()
API_HEADERS = {
	"Content-type": "application/json", 
	"Authorization": "Bearer {access_token}"
}
	
class KubernetesToilWorkflow(Job):
	def __init__(self, workflow_name, project_id, zone, node_num, machine_type, cluster_node_disk_size, secrets=None, network="default", logging_service=None, monitoring_service=None, tear_down=False):
		super(KubernetesToilWorkflow, self).__init__()
		self.workflow_name = workflow_name.replace("_", "-")
		self.project_id = project_id
		self.zone = zone
		self.cluster_endpoint = None
		self.cluster_admin_password = self.create_cluster_admin_password()
		self.cluster_spec = {
			"cluster": {
				"name": "{cluster_name}".format(cluster_name=self.workflow_name),
				"zone": "{zone}".format(zone=zone),
				"initialNodeCount": node_num,
				"network": "{network}".format(network=network),
				"nodeConfig": {
					"machineType": "{machine_type}".format(machine_type=machine_type),
					"diskSizeGb": cluster_node_disk_size,
					"oauthScopes": [
						"https://www.googleapis.com/auth/compute", 
						"https://www.googleapis.com/auth/devstorage.read_write", 
						"https://www.googleapis.com/auth/logging.write", 
						"https://www.googleapis.com/auth/cloud-platform"
					]
				},
				"masterAuth": {
	 				"username": "admin",
					"password": "{password}".format(password=self.cluster_admin_password),
				}
			}
		}

		if logging_service is not None:
			self.cluster_spec["cluster"]["loggingService"] = logging_service

		if monitoring_service is not None:
			self.cluster_spec["cluster"]["monitoringService"] = monitoring_service

		self.namespace_spec = {
			"apiVersion": "v1",
			"kind": "Namespace",
			"metadata": {
				"name": self.workflow_name
			}
		}
		
		self.secret_spec = {
			"kind": "Secret",
			"apiVersion": "v1",
			"metadata": {
			},
			"type": "Opaque",
			"data": {
			}
		}

		self.default_secret = ("refresh-token", base64.b64encode(CREDENTIALS.refresh_token), "/data-access")
		self.add_secrets = [self.default_secret]
		if secrets is not None:
			for secret in secrets:
				self.add_secrets.append((secret["name"], self.get_secret_contents(secret["url"]), secret["mount_path"]))
		
		self.cluster_hosts = []
		self.headers = API_HEADERS
		self.headers["Authorization"].format(access_token=CREDENTIALS.access_token)
		self.tear_down = tear_down
		if self.tear_down != "false" and self.tear_down is not False:
			cleanup = KubernetesToilWorkflowCleanup(self.workflow_name, self.project_id, self.zone)
			self.addFollowOn(cleanup)
		
	def run(self, filestore): 
		if CREDENTIALS.access_token_expired:
			CREDENTIALS.refresh(HTTP)
			self.headers["Authorization"].format(access_token=CREDENTIALS.access_token)

		filestore.logToMaster("{timestamp}  Starting workflow {workflow_name} ...".format(timestamp=self.create_timestamp(), workflow_name=self.workflow_name))
		self.ensure_cluster(filestore)
		filestore.logToMaster("{timestamp}  Cluster created successfully!".format(timestamp=self.create_timestamp()))
		self.configure_cluster_access(filestore) 
		filestore.logToMaster("{timestamp}  Cluster configured successfully!".format(timestamp=self.create_timestamp()))
		self.create_secret(self.default_secret, filestore)
		filestore.logToMaster("{timestamp}  Default secret created successfully!".format(timestamp=self.create_timestamp()))
		for secret in self.add_secrets:
			self.create_secret(secret, filestore)
		filestore.logToMaster("{timestamp}  Additional secrets created successfully!".format(timestamp=self.create_timestamp()))

		return (self.cluster_hosts, self.add_secrets)

	def create_timestamp(self):
		return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')

	def cluster_exists(self, filestore):
		cluster_exists = False
		try:
			response = GKE.projects().zones().clusters().get(projectId=self.project_id, zone=self.zone, clusterId=self.cluster_spec["cluster"]["name"]).execute(http=HTTP)
		except HttpError:
			pass
		else:
			# make sure the existing cluster meets the requirements in the given specification
			try:
				if str(response["name"]) == str(self.cluster_spec["cluster"]["name"]) and str(response["initialNodeCount"]) == str(self.cluster_spec["cluster"]["initialNodeCount"]) and str(response["nodeConfig"]["diskSizeGb"]) == str(self.cluster_spec["cluster"]["nodeConfig"]["diskSizeGb"]) and str(response["nodeConfig"]["machineType"]) == str(self.cluster_spec["cluster"]["nodeConfig"]["machineType"]):
					self.cluster_endpoint = response["endpoint"]
					cluster_exists = True
			except KeyError:
				pass

		return cluster_exists
					

	def ensure_cluster(self, filestore):
		# create a cluster to run the workflow on if it doesn't exist already
		if not self.cluster_exists(filestore):
			filestore.logToMaster("{timestamp}  Creating cluster ... ".format(timestamp=self.create_timestamp()))
			create_cluster = GKE.projects().zones().clusters().create(projectId=self.project_id, zone=self.zone, body=self.cluster_spec).execute(http=HTTP)
		
			# wait for the operation to complete
			while True:
				response = GKE.projects().zones().operations().get(projectId=self.project_id, zone=self.zone, operationId=create_cluster["name"]).execute(http=HTTP)
				
				if response['status'] == 'DONE':
					break
				else:
					time.sleep(1)

	def configure_cluster_access(self, filestore):
		# configure cluster access (may want to perform checks before doing this)
		filestore.logToMaster("{timestamp}  Configuring access to cluster {cluster_name} ...".format(timestamp=self.create_timestamp(), cluster_name=self.workflow_name))

		# configure ssh keys
		try:
			subprocess.check_call(["bash", "-c", "stat ~/.ssh/google_compute_engine && stat ~/.ssh/google_compute_engine.pub"])
		except subprocess.CalledProcessError as e:
			try:
				subprocess.check_call(["gcloud", "compute", "config-ssh"])
			except subprocess.CalledProcessError as e:
				filestore.logToMaster("Couldn't generate SSH keys for the workstation: {e}".format(e=e))
				exit(-1)
		
		try:
			subprocess.check_call(["gcloud", "config", "set", "compute/zone", self.zone])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't set the compute zone: {reason}".format(reason=e))
			exit(-1)
		try:
			subprocess.check_call(["kubectl", "config", "set", "cluster", self.workflow_name])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't set cluster in configuration: {reason}".format(reason=e))
			exit(-1) # raise an exception

		try:
			subprocess.check_call(["gcloud", "container", "clusters", "get-credentials", self.workflow_name])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't get cluster credentials: {reason}".format(reason=e))
			exit(-1) # raise an exception
			
		# get the cluster hosts for reference
		try:
			instance_group_name = subprocess.check_output(["gcloud", "compute", "instance-groups", "list", "--regexp", "^gke-{workflow}-.*-group$".format(workflow=self.workflow_name)]).split('\n')[1].split(' ')[0]
			instance_list = subprocess.check_output(["gcloud", "compute", "instance-groups", "list-instances", instance_group_name]).split('\n')[1:-1]
			for instance in instance_list:
				self.cluster_hosts.append(instance.split(' ')[0])

		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't get cluster hostnames: {reason}".format(reason=e))
			exit(-1) # raise an exception
	
		# run kubectl in proxy mode in a background process
		try:
			subprocess.Popen(["kubectl", "proxy", "--port", "8080"])
		except ValueError as e:
			exit(-1) # raise an exception

		# make sure the proxy is running -- something is going wrong here that I can't figure out.
		timeout = 180
		while True:
			try:
				response = SESSION.get(API_ROOT + NAMESPACE_URI)
			except:
				continue

			if response.status_code == 200:
				break

			if timeout <= 0:
				filestore.logToMaster("Couldn't access proxy (timeout reached): {status}".format(status=response.content))
				exit(-1)
			else:
				time.sleep(1)
				timeout -= 1

		# create a namespace for the workflow
		full_url = API_ROOT + NAMESPACE_URI
		response = SESSION.post(full_url, headers=self.headers, json=self.namespace_spec)
		
		# if the response isn't what's expected, raise an exception
		if response.status_code != 201:
			if response.status_code == 409: # already exists
				pass
			else:
				filestore.logToMaster("Namespace creation failed: {reason}".format(reason=response.status_code))
				exit(-1) # probably should raise an exception

		# set the namespace for the current context if it doesn't exist already
		kubectl_config = subprocess.Popen(["kubectl", "config", "view"], stdout=subprocess.PIPE)
		grep = subprocess.Popen(["grep", "current-context"], stdout=subprocess.PIPE, stdin=kubectl_config.stdout, stderr=subprocess.STDOUT)

		kubectl_context_string = grep.communicate()
		kube_context = kubectl_context_string[0].split(' ')[1].strip()
		try:
			subprocess.check_call(["kubectl", "config", "set", "contexts.{context}.namespace".format(context=kube_context), self.namespace_spec["metadata"]["name"]])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't set cluster context: {reason}".format(reason=e))
			exit(-1) # raise an exception

		filestore.logToMaster("{timestamp}  Cluster configuration was successful!".format(timestamp=self.create_timestamp()))

	def get_secret_contents(self, url):
		try:
			subprocess.check_output(["gsutil", "stat", url])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't get secret contents: {e}".format(e=e))
			exit(-1)
		
		try:
			contents = subprocess.check_output(["gsutil", "cat", url])
		except subprocess.CalledProcessError as e:
			filestore.logTomaster("Couldn't get secret contents: {e}".format(e=e))
			exit(-1)
	
		return base64.b64encode(contents)

	def create_secret(self, secret, filestore):
		secret_spec = self.secret_spec.copy()
		secret_spec["metadata"]["name"] = secret[0]
		secret_spec["data"] = {"{secret_name}".format(secret_name=secret[0]):"{secret_value}".format(secret_value=secret[1])}
		# create a secret
		full_url = API_ROOT + SECRETS_URI.format(namespace=self.namespace_spec["metadata"]["name"])
		response = SESSION.post(full_url, headers=self.headers, json=secret_spec)

		if response.status_code != 201:
			if response.status_code == 409: # already exists
				pass
			else:
				filestore.logToMaster("Secret creation failed: {reason}".format(reason=response.status_code))
				exit(-1) # probably should raise an exception

	def create_cluster_admin_password(self):
		return ''.join(SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))	
		

class KubernetesToilWorkflowCleanup(Job):
	def __init__(self, workflow_name, project_id, zone):
		super(KubernetesToilWorkflowCleanup, self).__init__()
		self.workflow_name = workflow_name.replace("_", "-")
		self.project_id = project_id
		self.zone = zone
		
	def run(self, filestore): 
		if CREDENTIALS.access_token_expired:
			CREDENTIALS.refresh(HTTP)
		
		self.cluster_cleanup(filestore)

		return True

	def cluster_cleanup(self, filestore):
		delete_cluster = GKE.projects().zones().clusters().delete(projectId=self.project_id, zone=self.zone, clusterId=self.workflow_name).execute(http=HTTP)

class KubernetesToilComputeJob(Job):
	def __init__(self, workflow_name, project_id, zone, job_name, container_image, container_script, additional_info, subworkflow_name=None, host_key=None, restart_policy="Never", cpu_limit=None, memory_limit=None, disk=None):
		super(KubernetesToilComputeJob, self).__init__()
		self.workflow_name = workflow_name.replace("_", "-")
		self.project_id = project_id
		self.zone = zone
		self.headers = API_HEADERS
		self.headers["Authorization"].format(access_token=CREDENTIALS.access_token)
		self.job_name = job_name.replace("_", "-")

		if subworkflow_name is None:
			self.host_path = "{job_name}-data".format(job_name=self.job_name)
		else:
			self.host_path = "{subworkflow_name}-data".format(subworkflow_name=subworkflow_name)

		self.job_spec = {
			"kind": "Pod",
			"apiVersion": "v1",
			"metadata": {
				"name": "{job_name}-{suffix}".format(job_name=self.job_name, suffix=''.join(SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(6))),
				"labels": {
					"workflow": "{workflow}".format(workflow=self.workflow_name)
				}
			},
			"spec": {
				"containers": [
					{
						"name": "{job_name}".format(job_name=self.job_name),
						"image": container_image,
						"command": ["sh", "-c", container_script],
						"workingDir": "/workflow",
						"volumeMounts": [
							{
								"name": "data".format(job_name=self.job_name),
								"mountPath": "/workflow",
								"readOnly": False	
							}
						]
					},

				],
				"volumes": [
					{
						"name": "data".format(job_name=self.job_name),
						"hostPath": {
							"path": "/{host_path}".format(host_path=self.host_path)
						}
					}
				],
				"restartPolicy": restart_policy
			}
		}
							
		self.restart_policy = restart_policy
		
		if cpu_limit is not None:
			self.job_spec["spec"]["containers"][0]["resources"] = { "cpu" : cpu_limit }
			
		if memory_limit is not None:
			self.job_spec["spec"]["containers"][0]["resources"] = {"memory": "{memory}G".format(memory=memory_limit)}

					
		self.host_key = host_key
		self.additional_info = additional_info

	def run(self, filestore):
		filestore.logToMaster("{timestamp}  Creating host directory for job data ...".format(timestamp=self.create_timestamp()))
		cluster_hosts = self.additional_info[0]
		secrets = self.additional_info[1]

		filestore.logToMaster(' '.join(map(str, self.additional_info)))
		if self.host_key is not None:
			self.job_spec["spec"]["nodeName"] = cluster_hosts[self.host_key]
			self.create_host_path(cluster_hosts[self.host_key])

		for secret in secrets:
			secret_volume_mount = {
				"name": secret[0],
				"mountPath": secret[2],
				"readOnly": True
			}
			self.job_spec["spec"]["containers"][0]["volumeMounts"].append(secret_volume_mount)
			secret_volume = {
				"name": secret[0],
				"secret": {
					"secretName": secret[0]
				}
			}
			self.job_spec["spec"]["volumes"].append(secret_volume)
			
		filestore.logToMaster("{timestamp}  Starting job {job_name} ...".format(timestamp=self.create_timestamp(), job_name=self.job_spec["metadata"]["name"]))
		submit = self.start_job(filestore) 
		filestore.logToMaster("{timestamp}  Job submission response: {submit}".format(timestamp=self.create_timestamp(), submit=submit.text))
		job_status = self.wait_for_job(filestore)
		filestore.logToMaster("{timestamp}  Job status response: {status}".format(timestamp=self.create_timestamp(), status=job_status.text))

		return job_status

	def create_host_path(self, host):
		try:
			subprocess.check_call(["gcloud", "compute", "ssh", host, "--command", "if [[ ! -d /{host_path} ]]; then sudo mkdir /{host_path}; fi".format(host_path=self.host_path)])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't create the hostPath directory for this job: {e}".format(e=e))
			exit(-1)

	def start_job(self, filestore):
		if CREDENTIALS.access_token_expired:
			CREDENTIALS.refresh(HTTP)
			self.headers["Authorization"].format(access_token=CREDENTIALS.access_token)

		full_path =  API_ROOT + PODS_URI.format(namespace=self.workflow_name)
		response = SESSION.post(full_path, headers=self.headers, json=self.job_spec)
		filestore.logToMaster("Job submission response: {response}".format(response=response))
		if response.status_code != 201:
			filestore.logToMaster("Job submission failed: {reason}".format(reason=response.content))
			exit(-1) #raise exception
			
		return response

	def wait_for_job(self, filestore):
		full_path = API_ROOT + PODS_URI.format(namespace=self.workflow_name) + "{job_name}".format(job_name=self.job_spec["metadata"]["name"])
		while True:
			# check the status of the job, and get the logs
			response = SESSION.get(full_path)

			if "phase" in response.json()["status"].keys() and response.json()["status"]["phase"] == "Succeeded":
				filestore.logToMaster("Job {jobname} succeeded!".format(jobname=self.job_spec["metadata"]["name"]))
				break
			elif "phase" in response.json()["status"].keys() and response.json()["status"]["phase"] == "Failed":
				if self.restart_policy == "Never":
					filestore.logToMaster("Job {jobname} failed: {reason}".format(jobname=self.job_spec["metadata"]["name"], reason=response.json()["status"]["containerStatuses"][0]["state"]["terminated"]["reason"]))
					exit(-1)
			elif "phase" in response.json()["status"].keys() and response.json()["status"]["phase"] == "Unknown":
					filestore.logToMaster("An unknown problem occurred with job {jobname}".format(jobname=self.job_spec["metadata"]["name"]))
					exit(-1)
			else:
				continue
				
		
		return response	

	def create_timestamp(self):
		return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')


			

		
		
			
		
		

