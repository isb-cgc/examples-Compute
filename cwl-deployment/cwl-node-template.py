import yaml
import sys

def GenerateStartupScript(path):
  script = open(path, 'r')
  script_contents = script.read()
  script.close()

  return script_contents

def GenerateConfig(context):
  resources_dict = {
    'resources': [
      {
        'name': '{name}'.format(name=context.env["name"]),
        'type': 'compute.v1.instance',
        'properties': {
          'metadata': {
            'items': [
              {
                'key': 'startup-script',
                'value': '{startupScript}'.format(startupScript=GenerateStartupScript(context.properties["startupScript"])),
              }
            ]
          },
          'zone': '{zone}'.format(zone=context.properties["zone"]),
          'machineType': 'https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/machineTypes/{machineType}'.format(project=context.env["project"], zone=context.properties["zone"], machineType=context.properties["machineType"]),
          'disks': [
            {
              'deviceName': 'boot',
              'type': 'PERSISTENT',
              'boot': True,
              'autoDelete': True,
              'initializeParams': {
                'sourceImage': 'https://www.googleapis.com/compute/v1/projects/google-containers/global/images/{containerVmName}'.format(containerVmName=context.properties["containerVmName"]),
                'diskSizeGb': '{diskSizeGb}'.format(diskSizeGb=context.properties["bootDiskSizeGb"]),
                'diskType':'https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/diskTypes/{bootDiskType}'.format(project=context.env["project"], zone=context.properties["zone"], bootDiskType=context.properties['bootDiskType'])
              }
            }
          ],
          'networkInterfaces': [
            {
              'network': 'https://www.googleapis.com/compute/v1/projects/{project}/global/networks/default'.format(project=context.env["project"]),
              'accessConfigs': [
                {
                  'name': 'External NAT',
                  'type': 'ONE_TO_ONE_NAT'
                }
              ]
            }
          ], 
        }
      }
    ]
  }
  print yaml.dump(resources_dict)
  return yaml.dump(resources_dict)


def main():
  alias=sys.argv[1]
  containerImage=GetLatestContainerImage(alias)
  print containerImage

if __name__ == "__main__":
  main()
