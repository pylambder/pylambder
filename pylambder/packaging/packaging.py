"""Module responsible for packaging code and dependencies for upload"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePath
from typing import List, Union

from pylambder import APP_NAME

PathOrString = Union[Path, str]

PREFIX = PurePath('python/lib/python3.7/site-packages')


def create_packages_archive(target_path: str, package_specs: List[str]) -> None:
    """Obtains specified packages and puts them in a zip file
    ready to by uploaded to AWS

    :param target_path: path for the archive. Should not contain the ".zip" suffix
    :param package_specs: list of package names with optional
        version restrictions
    """

    with tempfile.TemporaryDirectory(prefix=APP_NAME + "-") as tempdir:
        # TODO perhaps use `pip download` rather than `pip install`
        with zipfile.ZipFile(target_path, mode='w') as zf:
            if package_specs:
                pip_command = ['pip', 'install', '-t', tempdir] + package_specs
                subprocess.check_call(pip_command)
                _recursive_zip_write(zf, Path(tempdir), Path(tempdir), PREFIX)
            else:
                # write empty file to the archive to prevent AWS complaining
                # about empty zip
                zf.writestr('PYLAMBDER_EMPTY', 'EMPTY')


def create_project_archive(target_path: PathOrString, base_path: PathOrString,
                           project_dirs: List[PathOrString], ignored: List[PathOrString] = None):
    """Obtains specified packages and puts them in a zip file
    ready to by uploaded to AWS

    :param target_path: path for the archive. Should contain the ".zip"
        suffix
    :param base_path: common root for the packaged files
    :param project_dirs: list of directories to put in the archive
    :param ignored: List of directory and file paths, relative to base_path,
        which should not be present in the result archvie (nor their children)
    """

    # TODO Allow filtering files by glob, e.g. '*.pyc'
    if ignored is None:
        ignored = []

    base_path = Path(base_path)
    with zipfile.ZipFile(target_path, mode='w') as zf:
        for dir in project_dirs:
            _recursive_zip_write(zf, Path(base_path), Path(dir), PREFIX, ignored)


def _recursive_zip_write(zf: zipfile.ZipFile, relative_to: Path, dir: Path,
                         common_prefix='.', ignored=None):
    if ignored is None:
        ignored = []
    ignored = [PurePath(i) for i in ignored]
    common_prefix = PurePath(common_prefix)

    for dirpath, _subdirs, subfiles in os.walk(relative_to / dir):
        dirpath = Path(dirpath)

        for subdir in sorted(['.'] + subfiles):
            full_path = dirpath / subdir
            packaged_path = full_path.relative_to(relative_to)
            if not any(is_subpath(packaged_path, i) for i in ignored):
                zf.write(full_path, common_prefix / packaged_path)


def is_subpath(sub: PathOrString, ancestor: PathOrString) -> bool:
    """Returns True if sub is equal to ancestor or its subpath"""
    try:
        PurePath(sub).relative_to(PurePath(ancestor))
        return True
    except ValueError:
        return False
