"""Config loader. Global for now. Config file is loaded upon first use.
The file is key=value pairs, one per line."""

import logging
import sys

logger = logging.getLogger(__name__)

class MissingConfig(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

S3BUCKET = None 
CLOUDFORMATION_STACK  = None
AWS_LOGIN = None
AWS_PASSWORD = None

def load_config():
    try:
        import pylambder_config
        S3BUCKET = pylambder_config.s3bucket
        CLOUDFORMATION_STACK = pylambder_config.cloudformation_stack
        AWS_LOGIN = pylambder_config.aws_login
        AWS_PASSWORD = pylambder_config.aws_password

    except AttributeError as attribute_err:
        raise MissingConfig("Some values are missing in your pylambder config file.", attribute_err) from None

    except ImportError as import_err:
        raise MissingConfig("Pylambder config is missing", import_err) from None