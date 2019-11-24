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


S3BUCKET = None
CLOUDFORMATION_STACK = None
AWS_LOGIN = None
AWS_PASSWORD = None


def load_config():
    sys.path.insert(0, os.getcwd())
    try:
        global S3BUCKET
        global CLOUDFORMATION_STACK
        global AWS_LOGIN
        global AWS_PASSWORD

        import pylambder_config
        S3BUCKET = pylambder_config.s3bucket
        CLOUDFORMATION_STACK = pylambder_config.cloudformation_stack
        AWS_LOGIN = pylambder_config.aws_login
        AWS_PASSWORD = pylambder_config.aws_password
        if S3BUCKET is None:
            raise MissingConfig('Pylambder config "s3bucket" is missing')
        if CLOUDFORMATION_STACK is None:
            raise MissingConfig('Pylambder config "cloudformation_stack" is missing')

    except AttributeError as attribute_err:
        raise MissingConfig("Some values are missing in your pylambder config file.", attribute_err) from None

    except ImportError as import_err:
        raise MissingConfig("Pylambder config is missing", import_err) from None

    finally:
        # revert changes to sys.path
        sys.path.remove(os.getcwd())
