import time
import boto3
import sys
import hashlib
import datetime
from typing import List
from botocore.exceptions import ClientError
from pathlib import Path

cf_client = boto3.client('cloudformation')
cf_resource = boto3.resource('cloudformation')
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
def changeSetStatus(change_set_name, cf_client):
        response = cf_client.describe_change_set(
            ChangeSetName=change_set_name,
        )
        return response['Status'], response.get('StatusReason', '')


def file_md5sum(path):
    archive = open(path, 'rb').read()
    return str(hashlib.md5(archive).hexdigest())


def upload_if_missing(path) -> Uri:
    # @TODO handle missing local file
    local_md5 = file_md5sum(path)
    obj_key = URI_PREFIX + local_md5
    needs_upload = True
    try:
        obj = s3_resource.Object(BUCKET, obj_key)
        etag = obj.e_tag.strip('"') # e_tag from boto3 is wrapped in quotes
        print('etag of {} is {}'.format(obj_key, etag))
        print('local md5:', local_md5, local_md5.__class__)

        if '-' in etag:
            # the etag is a result of multipart upload (i.e. not the files md5)
            # skip check, satisfied by the object name matching local hash
            needs_upload = False
        else:
            needs_upload = etag != local_md5
        print("needs upload:", needs_upload)
    except Exception as ex:
        # ignore errors about (maybe) existing object, reupload
        pass

    if needs_upload:
        print("Uploading {} as {}".format(path, obj_key))
        s3_client.upload_file(str(path), BUCKET, obj_key)
    else:
        print("Skipping upload of {}: already exists as {}".format(path, obj_key))
    return F's3://{BUCKET}/{obj_key}'



def upload_functions() -> List[Uri]:
    """Expects functions zips to exist""config
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


def stack_exists(name) -> bool:
    try:
        stack = cf_resource.Stack(name)

        # Empty stack with state REVIEW_IN_PROGRESS appears when change set is
        # created. It is not deemed existing for the purposes of CREATE/UPDATE
        # changeset distinction.
        return stack.stack_status != 'REVIEW_IN_PROGRESS'
    except ClientError as ex:
        print("Client error: ", ex)
        return False


def wait_for_changeset_execution(stackname):
    stack = cf_resource.Stack(stackname)
    while True:
        stack.reload()
        print("stack status:", stack.stack_status)
        if stack.stack_status not in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
            break
        time.sleep(5)

def main():
    # Create change set
    print("Creating change set...")

    uris = upload_functions()
    uris.update(upload_layers())
    print(uris)
    template_body = template_body_format_str.format(**uris)
    print(template_body)

    operation = 'UPDATE' if stack_exists(stackname) else 'CREATE'
    print("exists:", stack_exists(stackname), 'operation:', operation)

    cs_name = F"{stackname}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}"
    print("changeset name: ", cs_name)

    cs_response = cf_client.create_change_set(
        StackName=stackname,
        TemplateBody=template_body,
        Parameters=params,
        Capabilities=[capabilities],
        ChangeSetType=operation,
        ChangeSetName=cs_name
    )

    print("Create change set response:", cs_response)
    change_set_name = cs_response['Id']

    # Wait until change set status is CREATE_COMPLETE
    while True:
        response, reason = changeSetStatus(change_set_name, cf_client)
        print("change set status:", response, reason)
        if response == 'CREATE_COMPLETE':
                break
        if response == 'FAILED':
            if reason == 'No updates are to be performed.':
                print("Nothing to change.")
                sys.exit(0)
            else:
                sys.exit(1)
        time.sleep(5)

    # Execute change set
    print("Executing change set...")
    ex_response = cf_client.execute_change_set(
        ChangeSetName=change_set_name
    )
    print("Execute change set reponse:", ex_response)
    wait_for_changeset_execution(stackname)


if __name__ == '__main__':
    main()
