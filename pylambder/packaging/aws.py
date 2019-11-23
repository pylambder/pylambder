import hashlib
import logging
import time
from pathlib import Path
from typing import Union

import boto3
from botocore.exceptions import ClientError

cf_client = boto3.client("cloudformation")
cf_resource = boto3.resource("cloudformation")
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

PathOrString = Union[Path, str]
Uri = str

logger = logging.getLogger(__name__)


def upload_file_if_missing(bucket_name: str, file_path: PathOrString) -> Uri:
    """Upload a local file to given S3 bucket.
    The object name is the file's md5sum. If object with such name already
    exists the upload is skipped."""

    with open(file_path, 'rb') as f:
        file_bytes = f.read()
        return upload_bytes_if_missing(bucket_name, file_bytes)


def upload_bytes_if_missing(bucket_name: str, file_bytes) -> Uri:
    """Upload an object with given content to given S3 bucket.
    The object name is the file's md5sum. If object with such name already
    exists the upload is skipped."""

    obj_key = _bytes_md5sum(file_bytes)
    needs_upload = not _s3_object_exists(bucket_name, obj_key)

    if needs_upload:
        logger.info("Uploading file as {}".format(obj_key))
        # TODO Add ContentMD5: base64(md5)
        s3_client.put_object(Bucket=bucket_name, Body=file_bytes, Key=obj_key)
    else:
        logger.debug("Skipping upload: already exists as {}".format(obj_key))
    return f"s3://{bucket_name}/{obj_key}"


def create_change_set(stack_name, template, change_set_name) -> str:
    """Returns False if no changes are to be made, True otherwise"""
    operation = 'UPDATE' if _stack_exists(stack_name) else 'CREATE'

    cs_response = cf_client.create_change_set(
        StackName=stack_name,
        TemplateBody=template,
        Parameters=[],
        Capabilities=['CAPABILITY_IAM'],
        ChangeSetType=operation,
        ChangeSetName=change_set_name
    )
    logger.debug('Create change set result: %s', cs_response)
    change_set_arn = cs_response['Id']
    return change_set_arn


def execute_changeset(stack_name, change_set_arn):
    ex_response = cf_client.execute_change_set(
        ChangeSetName=change_set_arn
    )
    logger.debug("Execute change set reponse: {}".format(ex_response))
    wait_for_stack_update(stack_name)


def wait_for_change_set_creation(change_set_arn):
    """Returns False if no changes are to be made, True otherwise"""
    while True:
        response = cf_client.describe_change_set(
            ChangeSetName=change_set_arn,
        )
        status, reason = response['Status'], response.get('StatusReason', '')
        logger.debug("Change set status: %s %s", status, reason)
        if status == 'CREATE_COMPLETE':
            return True
        if status == 'FAILED':
            if reason == 'No updates are to be performed.':
                return False
            else:
                # TODO use pylambder exception
                raise RuntimeError('Change set creation failed')
        time.sleep(1)


def wait_for_stack_update(stack_name):
    stack = cf_resource.Stack(stack_name)
    while True:
        stack.reload()
        logger.debug(f"Stack '%s' status: %s", stack_name, stack.stack_status)
        if stack.stack_status not in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
            logger.info("Stack %s achieved status: %s", stack_name, stack.stack_status)
            break
        time.sleep(5)
    

def _s3_object_exists(bucket_name, key) -> bool:
    try:
        s3_resource.Object(bucket_name, key).load()
        return True
    except ClientError:
        return False


def _stack_exists(name) -> bool:
    try:
        stack = cf_resource.Stack(name)

        # Empty stack with state REVIEW_IN_PROGRESS appears when change set is
        # created. It is not deemed existing for the purposes of CREATE/UPDATE
        # changeset distinction.
        return stack.stack_status != 'REVIEW_IN_PROGRESS'
    except ClientError as ex:
        print("Client error: ", ex)
        return False



def _file_md5sum(path: Path) -> str:
    """Calculates md5sum of a file at given path"""
    content = path.read_bytes()
    return str(hashlib.md5(content).hexdigest())


def _bytes_md5sum(binary):
    return str(hashlib.md5(binary).hexdigest())
