import logging
import os
import pkg_resources
import datetime
from pathlib import Path

import pylambder.config as config
import pylambder.packaging.packaging as packaging
import pylambder.packaging.aws as aws

DEPS_FILE = Path('requirements.txt')
ARTIFACTS_DIR = Path('build/pylambder/')
PROJECT_ARCHIVE = ARTIFACTS_DIR / Path('project.zip')
DEPENDENCIES_ARCHIVE = ARTIFACTS_DIR / Path('requirements.zip')
DEPENDENCIES_ARCHIVE_VSN = ARTIFACTS_DIR / Path('requirements.txt.md5')

FUNCTION_NAMES = ['onconnect', 'ondisconnect', 'taskexecute', 'taskresult']
LAYERS = {
    'project-layer': PROJECT_ARCHIVE,
    'dependencies-layer': DEPENDENCIES_ARCHIVE,
}

logger = logging.getLogger(__name__)


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
    _deploy(application_dir, config.S3BUCKET, config.CLOUDFORMATION_STACK)
    logger.info("AWS deployment finished.")


def _package(application_dir: Path):
    """Prepare application for upload by creating zip packages."""
    project_archive_path = application_dir / PROJECT_ARCHIVE
    deps_archive_path = application_dir / DEPENDENCIES_ARCHIVE

    packaging.create_project_archive(project_archive_path, application_dir,
                                     [application_dir], [ARTIFACTS_DIR, '.git'])

    deps_file = _get_deps_file(application_dir)
    deps_list = _get_deps_list(deps_file)
    if not packaging.is_packages_archive_up_to_date(
            deps_archive_path, deps_list):
        logger.info('Downloading project dependencies listed in {}'.
                    format(deps_file))
        packaging.create_packages_archive(
            deps_archive_path, _get_deps_list(deps_file))
    else:
        logger.info('Dependencies package exists at {}'.format(str(deps_archive_path)))


def _get_deps_file(application_dir: Path) -> Path:
    return Path(application_dir) / DEPS_FILE


def _get_deps_list(deps_file: Path) -> [str]:
    if deps_file.is_file():
        with open(deps_file, 'r') as f:
            return [l.lstrip() for l in f if l.strip() != '']
    else:
        []


def _deploy(application_dir: Path, s3_bucket: str, stack_name: str):
    uris = _upload_pylambder(s3_bucket)
    uris.update(_upload_project(s3_bucket))
    template = format_template(uris)
    change_set_name = F"{stack_name}-{datetime.datetime.now().strftime('%Y%m%dT%H%M%S')}"
    change_set_arn = aws.create_change_set(stack_name, template, change_set_name)
    if not aws.wait_for_change_set_creation(change_set_arn):
        logger.info("Stack exists, no changes required")
        return
    aws.execute_changeset(stack_name, change_set_arn)


def _upload_pylambder(bucket_name: str):
    """Upload pylambder functions"""
    uris = {}
    for fun in FUNCTION_NAMES:
        zip_bytes = pkg_resources.resource_string('pylambder', f'packaged/{fun}.zip')
        uris[fun] = aws.upload_bytes_if_missing(bucket_name, zip_bytes)
    return uris


def _upload_project(bucket_name: str):
    """Upload pylambder functions"""
    uris = {}
    for layer, archive in LAYERS.items():
        uris[layer] = aws.upload_file_if_missing(bucket_name, archive)
    return uris


def format_template(uris: dict):
    template_body_format_str = pkg_resources.resource_string(
        'pylambder', 'sam-data/template.yaml.template').decode()
    return template_body_format_str.format(**uris)
