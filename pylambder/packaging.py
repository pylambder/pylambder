"""Module responsible for packaging code and dependencies for upload"""

from typing import List
import tempfile
import subprocess
import shutil
import os
from pylambder import APP_NAME


def create_packages_archive(target_path: str, package_specs: List[str]) -> None:
    """Obtains specified packages and puts them in a zip file
    ready to by uploaded to AWS

    :param target_path: path for the archive. Should not contain the ".zip" suffix
    :param package_specs: list of package names with optional
        version restrictions
    """

    if not package_specs:
        raise ValueError("Dependencies list must be nonempty")

    # @TODO make python version customizable
    prefix = 'python/lib/python3.7/site-packages/'
    with tempfile.TemporaryDirectory(prefix=APP_NAME + "-") as tempdir:
        installation_dir = os.path.join(tempdir, prefix)
        pip_command = ['pip', 'install', '-t', installation_dir] + package_specs
        subprocess.check_call(pip_command)

        # if file exists at target_path.zip it is overwritten
        shutil.make_archive(target_path, format='zip', root_dir=tempdir, base_dir='.')