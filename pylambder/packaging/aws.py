import hashlib
import logging
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
        upload_bytes_if_missing(bucket_name, file_bytes)


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


def _s3_object_exists(bucket_name, key) -> bool:
    try:
        s3_resource.Object(bucket_name, key).load()
        return True
    except ClientError:
        return False


def _file_md5sum(path: Path) -> str:
    """Calculates md5sum of a file at given path"""
    content = path.read_bytes()
    return str(hashlib.md5(content).hexdigest())


def _bytes_md5sum(binary):
    return str(hashlib.md5(binary).hexdigest())