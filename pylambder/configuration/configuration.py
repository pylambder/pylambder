import random
import string
from os.path import join
from pylambder.configuration import user_config_template


def generate_config_template(app_path='.'):
    config_path = join(app_path, 'pylambder_config.py')
    print(f"Creating config file: {config_path}")
    with open(config_path, "w") as config_file:
        template = user_config_template.basic_user_config_template
        api_token = generate_api_token()
        config_file.write(template.format(api_token=api_token))
    print("Config file created")


def generate_api_token() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
