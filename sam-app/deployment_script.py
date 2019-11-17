import time
import boto3
import sys
from pathlib import Path

client = boto3.client('cloudformation')
s3_client = boto3.client('s3')

BUCKET = 'wgeisler-sam'
stackname = "new-stack"
templateurl = ""
params = []
capabilities = "CAPABILITY_IAM"
template_body_format_str = open('template.yaml.template', 'r').read()
function_names = ['onconnect', 'ondisconnect', 'taskexecute', 'taskresult']
layer_names = ['dependencies-layer', 'project-layer']

# Helper function to retrieve change set status
def changeSetStatus(change_set_name, client):
    response = client.describe_change_set(
      ChangeSetName=change_set_name,
    )
    return response['Status']


def upload_functions():
  """Expects functions zips to exist"""
  for fun in function_names:
    file_name = F'{fun}.zip'
    print("Uploading {} to s3".format(file_name))
    s3_client.upload_file(str(file_name), BUCKET, file_name)

def upload_layers():
  # @TODO: reuse existing
  for layer in layer_names:
    file_name = F'{layer}.zip'
    file_path = Path('lambda-layers') / file_name
    print("Uploading {} to s3".format(file_name))
    s3_client.upload_file(str(file_path), BUCKET, file_name)


def main():
  # Create change set
  print("Creating change set...")

  upload_functions()
  upload_layers()

  uris = {name: F's3://{BUCKET}/{name}.zip' for name in function_names + layer_names}
  print(uris)
  template_body = template_body_format_str.format(**uris)
  print(template_body)
  cs_response = client.create_change_set(
    StackName=stackname,
    TemplateBody=template_body,
    Parameters=params,
    Capabilities=[capabilities],
    ChangeSetType="CREATE",
    ChangeSetName=stackname + "-cs"
  )

  print("Create change set response:", cs_response)
  change_set_name = cs_response['Id']

  # Wait until change set status is CREATE_COMPLETE
  while True:
    response = changeSetStatus(change_set_name, client)
    print("change set status:", str(response))
    if response == 'CREATE_COMPLETE':
        break
    if response == 'FAILED':
        sys.exit(1)
    time.sleep(5)

  # Execute change set
  print("Executing change set...")
  ex_response = client.execute_change_set(
    ChangeSetName=change_set_name
  )
  print("Execute change set reponse:", ex_response)

    ## TODO wait for changeset to finish

if __name__ == '__main__':
  main()
