from os.path import join
from pylambder.configuration import user_config_template

def generate_config_template(app_path='.'):
    config_path = join(app_path, 'pylambder_config.py') 
    print(f"Creating config file: {config_path}")
    with open(config_path, "w") as config_file:
        config_file.write(user_config_template.basic_user_config_template)
    print("Config file created")
        