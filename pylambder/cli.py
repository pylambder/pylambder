import logging
import sys

import pylambder.packaging.deployment as deployment


def main():
    pylambder_logger = logging.getLogger('pylambder')
    pylambder_logger.setLevel(logging.DEBUG)

    if len(sys.argv) < 2 or sys.argv[1] in ['help', '-h', '--help']:
        print("The CLI pylambder interface.")
        print("Available commands:\n")
        print("{:<10s} Upload the pylambder and user code to AWS".format('deploy'))
        sys.exit(0)

    elif sys.argv[1] == 'deploy':
        app_path = sys.argv[2] if len(sys.argv) >= 3 else '.'
        deployment.deploy(app_path)
