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
from random import SystemRandom

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
SESSION = requests.Session()
API_HEADERS = {
	"Content-type": "application/json", 
	"Authorization": "Bearer {access_token}"
}
	
class KubernetesToilWorkflow(Job):
	def __init__(self, workflow_name, project_id, zone, node_num, machine_type, cluster_node_disk_size, cluster_nfs_volume_size, network="default", logging_service=None, monitoring_service=None, tear_down=True):
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
		self.nfs_service_spec = {
			"kind": "Service",
			"apiVersion": "v1",
			"metadata": {
				"name": "nfs-server"
			},
			"spec": {
				"ports": [
					{
						"port": 2049
					}
				],
				"selector": {
			    		"role": "nfs-server"
				}
			}
		}

		self.nfs_service_controller_spec = {
			"apiVersion": "v1",
			"kind": "ReplicationController",
			"metadata": {
				"name": "nfs-server"
			},
			"spec": {
				"replicas": 1,
				"selector": {
					"role": "nfs-server"
				},
				"template": {
					"metadata": {
						"labels": {
							"role": "nfs-server"
						}
					},
					"spec": {
						"containers": [
							{
								"name": "nfs-server",
								"image": "gcr.io/google_containers/volume-nfs",
								"ports": [
									{
										"name": "nfs",
										"containerPort": 2049
									}
								],
								"securityContext": {
									"privileged": True
								}
							}
						]
					}
				}
			}
		}
		self.nfs_volume_spec = {
			"apiVersion": "v1",
			"kind": "PersistentVolume",
			"metadata": {
				"name": "nfs-{workflow}".format(workflow=self.workflow_name)
			},
			"spec": {
				"capacity": {
					"storage": "{size}G".format(size=cluster_nfs_volume_size)
				},
				"nfs": {
					"server": None,
					"path": "/"
				},
			"accessModes": [ "ReadWriteMany" ]
			}
		}

		self.nfs_volume_claim_spec = {
			"kind": "PersistentVolumeClaim",
			"apiVersion": "v1",
			"metadata": {
		  		"name": "nfs-{workflow}".format(workflow=self.workflow_name)
			},
			"spec": {
		  		"accessModes": [ "ReadWriteMany" ],
				"resources": {
					"requests": {
						"storage": "{size}G".format(size=cluster_nfs_volume_size)
					}
				}
			}
		}
		self.secret = {
			"kind": "Secret",
			"apiVersion": "v1",
			"metadata": {
				"name": "refresh-token",
			},
			"type": "Opaque",
			"data": {
				"refresh-token": base64.b64encode(CREDENTIALS.refresh_token)
			}
		}
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
		self.create_secret(filestore)
		filestore.logToMaster("{timestamp}  Secret created successfully!".format(timestamp=self.create_timestamp()))
		self.configure_nfs_share(filestore) 
		filestore.logToMaster("{timestamp}  NFS share created successfully!".format(timestamp=self.create_timestamp()))
		return True

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

	def create_secret(self, filestore):
		# create a secret
		full_url = API_ROOT + SECRETS_URI.format(namespace=self.namespace_spec["metadata"]["name"])
		response = SESSION.post(full_url, headers=self.headers, json=self.secret)

		if response.status_code != 201:
			if response.status_code == 409: # already exists
				pass
			else:
				filestore.logToMaster("Secret creation failed: {reason}".format(reason=response.status_code))
				exit(-1) # probably should raise an exception
			

	def configure_nfs_share(self, filestore):
		filestore.logToMaster("{timestamp}  Creating an NFS share (size: {size}) for the cluster ...".format(timestamp=self.create_timestamp(), size=self.nfs_volume_spec["spec"]["capacity"]["storage"]))
		
		# create the NFS service and rc
		full_url = API_ROOT + SERVICES_URI.format(namespace=self.namespace_spec["metadata"]["name"])
		response = SESSION.post(full_url, headers=self.headers, json=self.nfs_service_spec)

		# if the response isn't what's expected, raise an exception
		if response.status_code != 201:
			if response.status_code == 409: # already exists
				pass
			else:
				filestore.logToMaster("NFS service creation failed: {reason}".format(reason=response.content))
				exit(-1) # probably should raise an exception

		full_url = API_ROOT + REPLICATION_CONTROLLERS_URI.format(namespace=self.namespace_spec["metadata"]["name"])
		response = SESSION.post(full_url, headers=self.headers, json=self.nfs_service_controller_spec)
		
		if response.status_code != 201:
			if response.status_code == 409: # already exists
				pass
			else:
				filestore.logToMaster("NFS service contoller creation failed: {reason}".format(reason=response.content))
				exit(-1)

		# get the service endpoint
		full_url = API_ROOT + SERVICES_URI.format(namespace=self.namespace_spec["metadata"]["name"]) + self.nfs_service_controller_spec["metadata"]["name"]
		response = SESSION.get(full_url)
		
		# if the response isn't what's expected, raise an exception
		if response.status_code != 200:
			exit(-1) # probably should raise an exception
		
		self.cluster_endpoint = response.json()["spec"]["clusterIP"]

		# create an NFS persistent volume for this workflow
		self.nfs_volume_spec["spec"]["nfs"]["server"] = self.cluster_endpoint
		full_url = API_ROOT + PERSISTENT_VOLUMES_URI.format(namespace=self.namespace_spec["metadata"]["name"])
		response = SESSION.post(full_url, headers=self.headers, json=self.nfs_volume_spec)
		
		# if the response isn't what's expected, raise an exception
		if response.status_code != 201:
			if response.status_code == 409: # already exists
				pass
			else:
				filestore.logToMaster("NFS persistent volume creation failed: {reason}".format(reason=response.content))
				exit(-1) # probably should raise an exception
		
		# create a persistent volume claim for the NFS volume
		full_url = API_ROOT + PERSISTENT_VOLUME_CLAIMS_URI.format(namespace=self.namespace_spec["metadata"]["name"])
		response = SESSION.post(full_url, headers=self.headers, json=self.nfs_volume_claim_spec)
		
		# if the response isn't what's expected, raise an exception
		if response.status_code != 201:
			if response.status_code == 409: # already exists
				pass
			else:
				filestore.logToMaster("NFS persistent volume claim creation failed: {reason}".format(reason=response.content))
				exit(-1) # probably should raise an exception

	def create_cluster_admin_password(self):
		return ''.join(SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))	
		

class KubernetesToilWorkflowCleanup(Job):
	def __init__(self, workflow_name, project_id, zone):
		super(KubernetesToilWorkflowCleanup, self).__init__()
		self.workflow_name = workflow_name.replace("_", "-")
		self.project_id = project_id
		self.zone = zone
		
	def run(self, filestore): # this should override the inherited "base" class run function
		if CREDENTIALS.access_token_expired:
			CREDENTIALS.refresh(HTTP)
		
		self.nfs_cleanup(filestore)
		self.cluster_cleanup(filestore)

		return True
	
	def nfs_cleanup(self, filestore):
		# delete the NFS volume and claim
		full_path = API_ROOT + PERSISTENT_VOLUME_CLAIMS_URI.format(namespace=self.workflow_name) + "nfs-{workflow}".format(workflow=self.workflow_name)
		response = SESSION.delete(full_path)

		# if the response isn't what's expected, raise an exception
		if response.status_code != 200:
			# if the response isn't what's expected, raise an exception
			filestore.logToMaster("NFS persistent volume claim deletion failed: {reason}".format(reason=response.content))
		
		full_path = API_ROOT + PERSISTENT_VOLUMES_URI.format(namespace=self.workflow_name) + "nfs-{workflow}".format(workflow=self.workflow_name)
		response = SESSION.delete(full_path)
		
		# if the response isn't what's expected, raise an exception
		if response.status_code != 200:
			filestore.logToMaster("NFS persistent volume deletion failed: {reason}".format(reason=response.content))

	def cluster_cleanup(self, filestore):
		# destroy the cluster
		delete_cluster = GKE.projects().zones().clusters().delete(projectId=self.project_id, zone=self.zone, clusterId=self.workflow_name).execute(http=HTTP)

class KubernetesToilComputeJob(Job):
	def __init__(self, workflow_name, job_name, container_image, container_script, restart_policy="Never", cpu_limit=None, memory_limit=None):
		super(KubernetesToilComputeJob, self).__init__()
		self.workflow_name = workflow_name.replace("_", "-")
		self.headers = API_HEADERS
		self.headers["Authorization"].format(access_token=CREDENTIALS.access_token)
		self.job_name = job_name.replace("_", "-")
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
								"name": "nfs-{workflow}".format(workflow=self.workflow_name),
								"mountPath": "/workflow/share"
							},
							{
								"name": "scratch",
								"mountPath": "/workflow/scratch"
							},
							{
								"name": "refresh-token",
								"mountPath": "/data-access",
								"readOnly": True
							}
						]
					},

				],
				"volumes": [
					{
						"name": "nfs-{workflow}".format(workflow=self.workflow_name),
						"persistentVolumeClaim": {
							"claimName": "nfs-{workflow}".format(workflow=self.workflow_name)
						}
					},
					{
						"name": "scratch",
						"emptyDir": {}
					},
					{
						"name": "refresh-token",
						"secret": {
							"secretName": "refresh-token"
						}
					}
				],
				"restartPolicy": restart_policy
			}
		}
		self.restart_policy = restart_policy
		
		if cpu_limit is not None:
			self.job_spec["spec"]["containers"]["resources"]["cpu"] = cpu_limit
			
		if memory_limit is not None:
			self.job_spec["spec"]["containers"]["resources"]["memory"] = "{memory}G".format(memory=memory_limit)
		

	def run(self, filestore):
		if self.host_key is not None:
			self.job_spec["spec"]["nodeName"] = self.cluster_hosts[self.host_key]
		filestore.logToMaster("{timestamp}  Starting job {job_name} ...".format(timestamp=self.create_timestamp(), job_name=self.job_spec["metadata"]["name"]))
		submit = self.start_job(filestore) 
		filestore.logToMaster("{timestamp}  Job submission response: {submit}".format(timestamp=self.create_timestamp(), submit=submit.text))
		job_status = self.wait_for_job(filestore)
		filestore.logToMaster("{timestamp}  Job status response: {status}".format(timestamp=self.create_timestamp(), status=job_status.text))

		return job_status

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


			

		
		
			
		
		
