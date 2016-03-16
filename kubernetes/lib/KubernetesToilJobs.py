import os
import pwd
import math
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

# GCP API Access
GKE = discovery.build('container', 'v1', http=HTTP)
COMPUTE = discovery.build('compute', 'v1', http=HTTP)
SESSION = requests.Session()
API_HEADERS = {
	"Content-type": "application/json", 
	"Authorization": "Bearer {access_token}"
}
	
class KubernetesToilWorkflow(Job):
	def __init__(self, workflow_name, project_id, zone, node_num, machine_type, cluster_node_disk_size, secrets=None, shared_files=None, network="default", logging_service=None, monitoring_service=None, tear_down=False):
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
				
		self.shared_files = shared_files
		
		cluster_nfs_volume_size = self.get_cluster_nfs_volume_size()
		
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
								},
								"volumeMounts": [
									{
										"name": "{workflow}-data".format(workflow=self.workflow_name),
										"mountPath": "/exports",
										"readOnly": False	
									}
								], 
								"resources": {
									"requests": {
										"cpu": int(self.cluster_spec["cluster"]["nodeConfig"]["machineType"].split('-')[-1]) - 1
									}
								}
							}
						],
						"volumes": [
							{
								"name": "{workflow}-data".format(workflow=self.workflow_name),
								"gcePersistentDisk": {
									"pdName": "{workflow}-data".format(workflow=self.workflow_name),
									"readOnly": False,
									"fsType": "ext4"
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
		
		self.nfs_disk_spec = { 
			"name": "{workflow}-data".format(workflow=self.workflow_name),
			"zone": "https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}".format(project=project_id, zone=zone), 
			"type": "https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/diskTypes/pd-ssd".format(project=project_id, zone=zone),
			"sizeGb": cluster_nfs_volume_size
		}
		
		self.cluster_hosts = []
		self.headers = API_HEADERS
		self.headers["Authorization"].format(access_token=CREDENTIALS.access_token)
		self.tear_down = tear_down
		if self.tear_down != "false" and self.tear_down is not False:
			cleanup = KubernetesToilWorkflowCleanup(self.workflow_name, self.project_id, self.zone, nfs=(self.shared_files is not None), nfs_disk_name=self.nfs_disk_spec["name"])
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
		
		if self.shared_files is not None:
			self.configure_nfs_share(filestore) 
			filestore.logToMaster("{timestamp}  NFS share created successfully!".format(timestamp=self.create_timestamp()))

		return (self.cluster_hosts, self.add_secrets)

	def create_timestamp(self):
		return datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		
	def get_cluster_nfs_volume_size(self, filestore):
		total_size = 0
		for shared_file in self.shared_files:
			try:
				filesize = subprocess.check_output(["gsutil", "du", shared_file])
			except subprocess.CalledProcessError as e:
				print "Couldn't get the filesize for file {filename}: {e}".format(filename=shared_file, e=e)
				exit(-1)
			
			total_size += int(filesize.split(' ')[0])
			
		return int(math.ceil(total_size/50000000000.0)*50000000000.0)
			

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
				
	def configure_nfs_share(self, filestore):
		filestore.logToMaster("{timestamp}  Creating an NFS share (size: {size}) for the cluster ...".format(timestamp=self.create_timestamp(), size=self.nfs_volume_spec["spec"]["capacity"]["storage"]))
		
		# create the persistent disk to back the NFS share
		try:
			get_disk = COMPUTE.disks().get(project=self.project_id, zone=self.zone, disk=self.nfs_disk_spec["name"]).execute()

		except HttpError:
			self.create_nfs_disk(filestore)
		
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
				filestore.logToMaster("NFS service controller creation failed: {reason}".format(reason=response.content))
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
			

	def create_nfs_disk(self, filestore):
		# Submit the disk request
		disk_response = COMPUTE.disks().insert(project=self.project_id, zone=self.zone, body=self.nfs_disk_spec).execute()

		# Wait for the disks to be created
		while True:
			result = COMPUTE.zoneOperations().get(project=self.project_id, zone=self.zone, operation=disk_response['name']).execute()
			if result['status'] == 'DONE':
				break

		# attach the disk to an instance for formatting
		attach_request = {
    			"kind": "compute#attachedDisk",
			"index": 1,
			"type": "PERSISTENT",
			"mode": "READ_WRITE",
			"source": "https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/disks/{disk_name}".format(project=self.project_id, zone=self.zone, disk_name=self.nfs_disk_spec["name"]),
			"deviceName": self.nfs_disk_spec["name"],
			"boot": False,
			"interface": "SCSI",
			"autoDelete": False
    		}

		for instance in self.cluster_hosts:
			success = False
			attach_response = COMPUTE.instances().attachDisk(project=self.project_id, zone=self.zone, instance=instance, body=attach_request).execute()

			# Wait for the attach operation to complete
			while True:
				result = COMPUTE.zoneOperations().get(project=self.project_id, zone=self.zone, operation=attach_response['name']).execute()
				if result['status'] == 'DONE':
					success = True
					break

			if success == True:
				break

		if success == False:
			filestore.logToMaster("Couldn't attach disk for formatting: {result}".format(result=result))
			exit(-1)
	
		# generate ssh keys on the workstation
		try:
			subprocess.check_call(["bash", "-c", "stat ~/.ssh/google_compute_engine && stat ~/.ssh/google_compute_engine.pub"])
		except subprocess.CalledProcessError as e:
			try:
				subprocess.check_call(["gcloud", "compute", "config-ssh"])
			except subprocess.CalledProcessError as e:
				filestore.logToMaster("Couldn't generate SSH keys for the workstation: {e}".format(e=e))
				exit(-1)

		command = "sudo mkdir -p /{workflow}-data && sudo mkfs.ext4 -F /dev/disk/by-id/google-{workflow}-data && sudo mount -o discard,defaults /dev/disk/by-id/google-{workflow}-data /{workflow}-data".format(workflow=self.workflow_name)
		try:
			subprocess.check_call(["gcloud", "compute", "ssh", instance, "--command", command])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't format the disk: {e}".format(e=e))
			exit(-1)

		detach_response = COMPUTE.instances().detachDisk(project=self.project_id, zone=self.zone, instance=instance, deviceName=self.nfs_disk_spec["name"]).execute()

		# Wait for the detach operation to complete
		while True:
			try:
				result = COMPUTE.zoneOperations().get(project=self.project_id, zone=self.zone, operation=detach_response['name']).execute()
			except HttpError:
				break
			else:
				if result['status'] == 'DONE':
					break
		
		filestore.logToMaster("Disk created successfully!")


	def create_cluster_admin_password(self):
		return ''.join(SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))	
		

class KubernetesToilWorkflowCleanup(Job):
	def __init__(self, workflow_name, project_id, zone, nfs=False, nfs_disk_name=None):
		super(KubernetesToilWorkflowCleanup, self).__init__()
		self.workflow_name = workflow_name.replace("_", "-")
		self.project_id = project_id
		self.zone = zone
		self.nfs = nfs
		self.nfs_disk_name = nfs_disk_name
		
	def run(self, filestore): 
		if CREDENTIALS.access_token_expired:
			CREDENTIALS.refresh(HTTP)
		
		self.cluster_cleanup(filestore)
		
		if self.nfs is True:
			self.nfs_disk_cleanup()

		return True

	def cluster_cleanup(self, filestore):
		delete_cluster = GKE.projects().zones().clusters().delete(projectId=self.project_id, zone=self.zone, clusterId=self.workflow_name).execute(http=HTTP)
		
	def nfs_disk_cleanup(self):
		delete_disk = COMPUTE.disks().delete(project=self.project_id, zone=self.zone, disk=self.nfs_disk_name).execute()

class KubernetesToilComputeJob(Job):
	def __init__(self, workflow_name, project_id, zone, job_name, container_image, container_script, additional_info, cleanup=False, subworkflow_name=None, host_key=None, restart_policy="Never", cpu_limit=None, memory_limit=None, disk=None):
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
						"command": ["bash", "-c", container_script],
						"workingDir": "/workflow",
						"volumeMounts": [
							{
								"name": "data".format(job_name=self.job_name),
								"mountPath": "/workflow",
								"readOnly": False	
							},
							{
								"name": "nfs-{workflow}".format(workflow=self.workflow_name),
								"mountPath": "/share",
								"readOnly": True
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
					},
					{
						"name": "nfs-{workflow}".format(workflow=self.workflow_name),
						"persistentVolumeClaim": {
							"claimName": "nfs-{workflow}".format(workflow=self.workflow_name)
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
		
		if cleanup is True:
			self.addFollowOn(KubernetesToilComputeJobCleanup(cluster_hosts[self.host_key], self.host_path))

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
		
class KubernetesToilComputeJobCleanup(Job):
	def __init__(self, host, host_path):
		super(KubernetesToilComputeJobCleanup, self).__init__()
		self.host = host
		self.host_path = host_path
	
	def run(self, filestore): 
		if CREDENTIALS.access_token_expired:
			CREDENTIALS.refresh(HTTP)
		
		self.delete_host_path(filestore)

		return True
		
	def delete_host_path(self, filestore):
		try:
			subprocess.check_call(["gcloud", "compute", "ssh", self.host, "--command", "if [[ -d /{host_path} ]]; then sudo rm -rf /{host_path}; fi".format(host_path=self.host_path)])
		except subprocess.CalledProcessError as e:
			filestore.logToMaster("Couldn't delete the hostPath directory for this job: {e}".format(e=e))
			exit(-1)


			

		
		
			
		
		

