"""Module responsible for packaging code and dependencies for upload"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import List, Union

from pylambder import APP_NAME

PathOrString = Union[Path, str]


def create_packages_archive(target_path: str, package_specs: List[str]) -> None:
    """Obtains specified packages and puts them in a zip file
    ready to by uploaded to AWS

    :param target_path: path for the archive. Should not contain the ".zip" suffix
    :param package_specs: list of package names with optional
        version restrictions
    """

    # @TODO make python version customizable
    prefix = 'python/lib/python3.7/site-packages/'
    with tempfile.TemporaryDirectory(prefix=APP_NAME + "-") as tempdir:
        installation_dir = os.path.join(tempdir, prefix)
        # TODO perhaps use `pip download` rather than `pip install`
        if package_specs:
            pip_command = ['pip', 'install', '-t', installation_dir] + package_specs
            subprocess.check_call(pip_command)

        with zipfile.ZipFile(target_path, mode='w') as zf:
            _recursive_zip_write(zf, Path(tempdir), Path(tempdir))


def create_project_archive(target_path: PathOrString, base_path: PathOrString,
                           project_dirs: PathOrString):
    """Obtains specified packages and puts them in a zip file
    ready to by uploaded to AWS

    :param target_path: path for the archive. Should contain the ".zip"
        suffix
    :param base_path: common root for the packaged files
    :param project_dirs: list of directories to put in the archive
    """

    # TODO Allow filtering files e.g. to skip .pyc

    base_path = Path(base_path)
    with zipfile.ZipFile(target_path, mode='w') as zf:
        for dir in project_dirs:
            _recursive_zip_write(zf, Path(base_path), Path(dir))


def _recursive_zip_write(zf: zipfile.ZipFile, relative_to: Path, dir: Path):
    for dirpath, subdirs, subfiles in os.walk(relative_to / dir):
        dirpath = Path(dirpath)

        for subdir in sorted(subdirs + subfiles):
            full_path = dirpath / subdir
            packaged_path = full_path.relative_to(relative_to)
            zf.write(full_path, packaged_path)
