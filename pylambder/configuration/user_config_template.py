basic_user_config_template = """
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