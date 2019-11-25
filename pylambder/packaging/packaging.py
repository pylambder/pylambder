"""Module responsible for packaging code and dependencies for upload"""

import logging
import os
import subprocess
import json
import tempfile
import zipfile
from pathlib import Path, PurePath
from typing import List, Union

from pylambder import APP_NAME

PathOrString = Union[Path, str]

PREFIX = PurePath('python/lib/python3.7/site-packages')
AWS_PLATFORM = 'manylinux1_x86_64'

ALWAYS_IGNORE_EXT = ['.pyc']
ALWAYS_IGNORE_PATH = ['__pycache__']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_packages_archive(target_path: str, deps_list) -> None:
    """Obtains specified packages and puts them in a zip file
    ready to by uploaded to AWS

    :param target_path: path for the archive. Should not contain the ".zip" suffix
    :param package_specs: list of package names with optional
        version restrictions
    """

    with tempfile.TemporaryDirectory(prefix=APP_NAME + "-") as tempdir, \
            zipfile.ZipFile(target_path, mode='w') as zf:
        deps_list = _filter_out_existing_packages(deps_list)
        zf.writestr('MANIFEST', json.dumps(sorted(deps_list)))
        if deps_list:
            pip_command = [
                'pip', 'install', '-t', tempdir,
                '--platform', AWS_PLATFORM, '--only-binary=:all:',
            ] + deps_list
            logger.debug
            subprocess.check_call(pip_command)
            _recursive_zip_write(zf, Path(tempdir), Path(tempdir), PREFIX)
        else:
            # write empty file to the archive to prevent AWS complaining
            # about empty zip
            zf.writestr('PYLAMBDER_EMPTY', 'EMPTY')


def is_packages_archive_up_to_date(archive_path: str, deps_list):
    new_deps_list = sorted(_filter_out_existing_packages(deps_list))
    try:
        with zipfile.ZipFile(archive_path, mode='r') as zf:
            manifest = zf.open('MANIFEST')
            old_deps_list = json.loads(manifest.read())
            return old_deps_list == new_deps_list
    except:
        return False


def _filter_out_existing_packages(deps_list):
    """Filter out packages supplied by a public AWS layer"""
    ignored_packages = ['numpy', 'scipy']
    return [dep for dep in deps_list if not any(ignore in dep for ignore in ignored_packages)]


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
            if not any(is_subpath(packaged_path, i) for i in ignored) \
                and not any(i in str(packaged_path) for i in ALWAYS_IGNORE_PATH) \
                    and not any(str(packaged_path)[-len(i):] == i for i in ALWAYS_IGNORE_EXT):
                zf.write(full_path, common_prefix / packaged_path)


def is_subpath(sub: PathOrString, ancestor: PathOrString) -> bool:
    """Returns True if sub is equal to ancestor or its subpath"""
    try:
        PurePath(sub).relative_to(PurePath(ancestor))
        return True
    except ValueError:
        return False
