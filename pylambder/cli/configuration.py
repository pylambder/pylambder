import random
import string
from os.path import join

USER_CONFIG_TEMPLATE = """
## Pylambder config ##
# This is a minimal config file you need for the pylambder library to work 
# AWS Names
s3bucket = "your-bucket-anem"
cloudformation_stack = "your-stack-name"

# Pylambder API credentials
api_token = "{api_token}"

# AWS Credentials
# Warning: Storing your credentials in plaintext is not recommended
aws_access_key_id = "aws-key-id"
aws_secret_access_key = "your-aws-secret"
"""


def generate_config_template(app_path='.'):
    config_path = join(app_path, 'pylambder_config.py')
    print(f"Creating config file: {config_path}")
    with open(config_path, "w") as config_file:
        api_token = generate_api_token()
        config_file.write(USER_CONFIG_TEMPLATE.format(api_token=api_token))
    print("Config file created")


def generate_api_token() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
