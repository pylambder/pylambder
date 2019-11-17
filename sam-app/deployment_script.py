import time
import boto3
import sys

client = boto3.client('cloudformation')
s3_client = boto3.client('s3')

BUCKET = 'wgeisler-sam'
stackname = ""
templateurl = ""
params = []
capabilities = "CAPABILITY_IAM"
template_body_format_str = open('template.yaml.template', 'r').read()
function_names = ['onconnect', 'ondisconnect', 'taskexecute', 'taskresult']

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
    print("Uploding {} to s3".format(file_name))
    s3_client.upload_file(file_name, BUCKET, file_name)


def main():
  # Create change set
  print("Creating change set...")

  upload_functions()

  uris = {fun: F's3://{BUCKET}/{fun}' for fun in function_names}
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
    time.sleep(10)

  # Execute change set
  print("Executing change set...")
  ex_response = client.execute_change_set(
    ChangeSetName=change_set_name
  )
  print("Execute change set reponse:", ex_response)

if __name__ == '__main__':
  main()