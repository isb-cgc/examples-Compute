import colander

MACHINE_TYPES = [
	"n1-standard-1",
	"n1-standard-2",
	"n1-standard-4",
	"n1-standard-8",
	"n1-standard-16",
	"n1-standard-32",
	"n1-highmem-2",
	"n1-highmem-4",
	"n1-highmem-8",
	"n1-highmem-16",
	"n1-highmem-32",
	"n1-highcpu-2",
	"n1-highcpu-4",
	"n1-highcpu-8",
	"n1-highcpu-16",
	"n1-highcpu-32",
	"f1-micro",
	"g1-small"
]
ZONES = [
	"us-east1-b",
	"us-east1-c",
	"us-east1-d",
	"us-central1-a",
	"us-central1-b",
	"us-central1-c",
	"us-central1-f",
	"europe-west1-b",
	"europe-west1-c",
	"europe-west1-d",
	"asia-east1-a",
	"asia-east1-b",
	"asia-east1-c"
]

JOBS_LIST = []

class Cluster(colander.MappingSchema):
	project_id = colander.SchemaNode(colander.String)
	zone = colander.SchemaNode(colander.String, validator=colander.OneOf(ZONES))
	node_num = colander.SchemaNode(colander.Int, validator=colander.Range(min=1))
	network = colander.SchemaNode(colander.String)
	machine_type = colander.SchemaNode(colander.String, validator=colander.OneOf(MACHINE_TYPES))
	cluster_node_disk_size = colander.SchemaNode(colander.Int)
	cluster_nfs_volume_size = colander.SchemaNode(colander.String, validator=colander.Regex("^(0\.[0-9]*|[1-9]{1}[0-9]*)(([E|P|T|G|M|K][i]?)|(m))?$"))
	logging_service = colander.SchemaNode(colander.String, missing=colander.drop)
	monitoring_service = colander.SchemaNode(colander.String, missing=colander.drop)

class Parents(colander.SequenceSchema):
	parent = colander.SchemaNode(colander.String, validator=colander.OneOf(JOBS_LIST), missing=colander.drop)

class Job(colander.MappingSchema):
	parents = Parents()
	container_image = colander.SchemaNode(colander.String)
	container_script = colander.SchemaNode(colander.String)
	restart_policy = colander.SchemaNode(colander.String, missing=colander.drop, validator=colander.OneOf(["OnFailure", "Always", "Never"]))

class Jobs(colander.SequenceSchema):
	job = Job()

class WorkflowConfig(colander.MappingSchema):
	cluster = Cluster()
	jobs = Jobs()

class Workflow(collander.MappingSchema):
	def __init__(self, jobs_list):
		global JOBS_LIST
		JOBS_LIST.extend(jobs_list)
		
	name = colander.SchemaNode(colander.String, validator=colander.Regex("")) # TODO: find list of acceptable characters
	cluster = Cluster()
	jobs = Jobs()
		

	
		

