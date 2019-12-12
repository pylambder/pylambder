"""Config loader. Global for now. Config file is loaded upon first use.
The file is key=value pairs, one per line."""

import logging
import os
import sys

logger = logging.getLogger(__name__)


class MissingConfig(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


loaded = False
S3BUCKET = None
CLOUDFORMATION_STACK = None
API_TOKEN = None
AWS_ACCESS_KEY_ID = None
AWS_ACCESS_KEY_SECRET = None


def ensure_loaded() -> None:
    if not loaded:
        load_config()


def load_config() -> None:
    sys.path.insert(0, os.getcwd())
    try:
        import pylambder_config

        global loaded
        global S3BUCKET
        global CLOUDFORMATION_STACK
        global API_TOKEN
        global AWS_ACCESS_KEY_ID
        global AWS_ACCESS_KEY_SECRET
    
        S3BUCKET = pylambder_config.s3bucket
        CLOUDFORMATION_STACK = pylambder_config.cloudformation_stack
        API_TOKEN = pylambder_config.api_token
        AWS_ACCESS_KEY_ID = pylambder_config.aws_access_key_id
        AWS_ACCESS_KEY_SECRET = pylambder_config.aws_access_key_secret

        if not S3BUCKET:
            raise MissingConfig('Pylambder config variable "s3bucket" is empty')
        if not CLOUDFORMATION_STACK:
            raise MissingConfig('Pylambder config variable "cloudformation_stack" is empty')
        if not API_TOKEN:
            raise MissingConfig('Pylambder config variable "api_token" is empty')
        if not AWS_ACCESS_KEY_ID:
            raise MissingConfig('Pylambder config variable "aws_access_key_id" is empty')
        if not AWS_ACCESS_KEY_SECRET:
            raise MissingConfig('Pylambder config variable "aws_access_key_secret" is empty')

        loaded = True

    except AttributeError as attribute_err:
        raise MissingConfig("Some values are missing in your pylambder config file.", attribute_err) from None

    except ImportError as import_err:
        raise MissingConfig("Pylambder config is missing", import_err) from None

    finally:
        # revert changes to sys.path
        sys.path.remove(os.getcwd())
