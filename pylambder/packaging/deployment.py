import logging
import os
from pathlib import Path

import pylambder.config as config
import pylambder.packaging.packaging as packaging

ARTIFACTS_DIR = Path('build/pylambder/')
PROJECT_ARCHIVE = ARTIFACTS_DIR / Path('project.zip')
DEPENDENCIES_ARCHIVE = ARTIFACTS_DIR / Path('requirements.zip')

logger = logging.getLogger(__name__)


def deploy(application_dir='.'):
    """Deploys the user application and pylambder on AWS.
    When this function finishes the AWS is ready to accept requests."""
    application_dir = Path(application_dir)
    os.makedirs(application_dir / ARTIFACTS_DIR, exist_ok=True)

    _package(application_dir)
    _upload(application_dir, config.get('s3bucket'))


def _package(application_dir: Path):
    project_archive_path = application_dir / PROJECT_ARCHIVE
    deps_archive_path = application_dir / DEPENDENCIES_ARCHIVE
    deps_list = _get_deps_list(application_dir)

    packaging.create_project_archive(project_archive_path, application_dir,
                                     [application_dir], [ARTIFACTS_DIR])

    logger.info('Downloading project dependencies:\n' + '\n'.join(deps_list))
    packaging.create_packages_archive(deps_archive_path, deps_list)


def _upload(application_dir: Path, s3_bucket: str):
    pass


def _get_deps_list(application_dir: Path) -> [str]:
    req_file = application_dir / 'requirements.txt'
    if req_file.is_file():
        with open(req_file, 'r') as f:
            return [l.lstrip() for l in f if l.strip() != '']

    else:
        []
