import time
import boto3
import sys
import hashlib
from typing import List
from botocore.exceptions import ClientError
from pathlib import Path

client = boto3.client('cloudformation')
s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

Uri = str

BUCKET = 'wgeisler-sam'
# TODO user version in the prefix or in object metadata to allow easier removal of outdated code
URI_PREFIX = 'pylambder/'
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


def file_md5sum(path):
    archive = open(path, 'rb').read()
    return str(hashlib.md5(archive).hexdigest())


def upload_if_missing(path) -> Uri:
    # @TODO handle missing local file
    local_md5 = file_md5sum(path)
    obj_key = URI_PREFIX + local_md5
    needs_upload = True
    try:
        # Asssume etag is the file's md5 - true unless
        # the file is over 5GiB or uploaded as multipar

        obj = s3_resource.Object(BUCKET, obj_key)
        etag = obj.e_tag.strip('"') # e_tag from boto3 is wrapped in quotes
        print('etag:', etag, etag.__class__)
        print('local md5:', local_md5, local_md5.__class__)
        needs_upload = etag != local_md5
        print("needs upload:", needs_upload)
    except Exception as ex:
        # ignore errors about (maybe) existing object, reupload
        pass

    if needs_upload:
        print("Uploading {} as {}".format(path, obj_key))
        s3_client.upload_file(str(path), BUCKET, obj_key)
    else:
        print("Skipping upload of {}: already exists as {}".format(path, local_md5))
    return F's3://{BUCKET}/{obj_key}'






def upload_functions() -> List[Uri]:
    """Expects functions zips to exist"""
    uris = dict()
    for fun in function_names:
        file_name = F'{fun}.zip'
        print("Uploading {} to s3".format(file_name))
        uris[fun] = upload_if_missing(file_name)
    return uris

def upload_layers() -> List[Uri]:
    uris = dict()
    for layer in layer_names:
        file_name = F'{layer}.zip'
        file_path = Path('lambda-layers') / file_name
        print("Uploading {} to s3".format(file_name))
        uris[layer] = upload_if_missing(str(file_path))
    return uris


def main():
    # Create change set
    print("Creating change set...")

    uris = upload_functions()
    uris.update(upload_layers())
    print(uris)
    template_body = template_body_format_str.format(**uris)
    print(template_body)
    cs_response = client.create_change_set(
        StackName=stackname,
        TemplateBody=template_body,
        Parameters=params,
        Capabilities=[capabilities],
        ChangeSetType="CREATE", # TODO check if stack exists and use UPDATE
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
