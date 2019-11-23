import logging
import os
import pkg_resources
from pathlib import Path

import pylambder.config as config
import pylambder.packaging.packaging as packaging
import pylambder.packaging.aws as aws

ARTIFACTS_DIR = Path('build/pylambder/')
PROJECT_ARCHIVE = ARTIFACTS_DIR / Path('project.zip')
DEPENDENCIES_ARCHIVE = ARTIFACTS_DIR / Path('requirements.zip')

FUNCTION_NAMES = ['onconnect', 'ondisconnect', 'taskexecute', 'taskresult']
LAYERS = {
    'project-layer': PROJECT_ARCHIVE,
    'dependencies-layer': DEPENDENCIES_ARCHIVE,
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def package(application_dir='.'):
    """Deploys the user application and pylambder on AWS.
    When this function finishes the AWS is ready to accept requests."""
    application_dir = Path(application_dir)
    os.makedirs(application_dir / ARTIFACTS_DIR, exist_ok=True)
    _package(application_dir)


def deploy(application_dir='.'):
    """Deploys the user application and pylambder on AWS.
    When this function finishes the AWS is ready to accept requests."""
    application_dir = Path(application_dir)
    os.makedirs(application_dir / ARTIFACTS_DIR, exist_ok=True)

    package(application_dir)
    _upload(application_dir, config.get('s3bucket'))


def _package(application_dir: Path):
    """Prepare application for upload by creating zip packages."""
    project_archive_path = application_dir / PROJECT_ARCHIVE
    deps_archive_path = application_dir / DEPENDENCIES_ARCHIVE
    deps_list = _get_deps_list(application_dir)

    packaging.create_project_archive(project_archive_path, application_dir,
                                     [application_dir], [ARTIFACTS_DIR, '.git'])

    logger.info('Downloading project dependencies:\n' + '\n'.join(deps_list))
    packaging.create_packages_archive(deps_archive_path, deps_list)


def _get_deps_list(application_dir: Path) -> [str]:
    req_file = application_dir / 'requirements.txt'
    if req_file.is_file():
        with open(req_file, 'r') as f:
            return [l.lstrip() for l in f if l.strip() != '']
    else:
        []


def _upload(application_dir: Path, s3_bucket: str):
    uris = _upload_pylambder(s3_bucket)
    uris.update(_upload_project(s3_bucket))


def _upload_pylambder(bucket_name: str):
    """Upload pylambder functions"""
    uris={}
    for fun in FUNCTION_NAMES:
        zipbytes=pkg_resources.resource_string('pylambder', f'packaged/{fun}.zip')
        uris[fun]=aws.upload_bytes_if_missing(bucket_name, zipbytes)
    return uris

def _upload_project(bucket_name: str):
    """Upload pylambder functions"""
    uris={}
    for layer, archive in LAYERS.items():
        uris[layer]=aws.upload_file_if_missing(bucket_name, archive)
    return uris
