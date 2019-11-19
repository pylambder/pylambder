import unittest
from unittest.mock import patch
import os
import zipfile
import tempfile
from pathlib import Path

import pylambder.packaging.packaging as packaging


class TestPackaging(unittest.TestCase):

    def test_empty_dependencies_create_empty_archive(self):
        with tempfile.TemporaryDirectory() as dir:
            archive_path = os.path.join(dir, "archive.zip")
            deps = []
            packaging.create_packages_archive(archive_path, deps)

            self.assertTrue(os.path.isfile(archive_path))
            zip = zipfile.ZipFile(archive_path)

            self.assertEqual([], zip.namelist())

    def test_dependencies_archive_creation(self):
        def pip_mock(command):
            self.assertEqual(['pip', 'install', '-t'],  command[0:3])
            dir = command[3]
            packages = command[4:]

            for p in packages:
                package_dir = os.path.join(dir, p)
                os.makedirs(package_dir)
                with open(os.path.join(package_dir, "stub"), "w") as f:
                    f.write("mocked file content\n")

        with patch('subprocess.check_call', side_effect=pip_mock) as mock_call:

            with tempfile.TemporaryDirectory() as dir:
                archive_path = os.path.join(dir, "archive.zip")
                deps = ["somepackage", "otherpackage"]
                packaging.create_packages_archive(archive_path, deps)

                self.assertTrue(os.path.isfile(archive_path))
                zip = zipfile.ZipFile(archive_path)

                expected = [
                    "python/lib/python3.7/site-packages/somepackage/",
                    "python/lib/python3.7/site-packages/somepackage/stub",
                    "python/lib/python3.7/site-packages/otherpackage/",
                    "python/lib/python3.7/site-packages/otherpackage/stub",
                ]
                for exp in expected:
                    self.assertIn(exp, zip.namelist())

    def test_archving_whole_project(self):
        with tempfile.TemporaryDirectory() as workdir, \
                tempfile.NamedTemporaryFile(suffix='.zip') as archive_file:
            archive_path = Path(archive_file.name)

            filenames = ['setup.py', 'pack1/app.py', 'pack1/utils.py',
                         'pack1/subpackage/code.py', 'pack2/code.py']
            _create_files(workdir, filenames)

            packaging.create_project_archive(archive_path, workdir, [workdir])

            self.assertTrue(archive_path.is_file(), f'{archive_path} is not a file')
            zip = zipfile.ZipFile(archive_path)

            files_in_zip = zip.namelist()
            for file in filenames:
                self.assertIn('python/lib/python3.7/site-packages/' + file, files_in_zip)

    def test_archving_selected_project_dirs(self):
        with tempfile.TemporaryDirectory() as workdir:
            dirpath = Path(workdir)
            archive_path = dirpath / 'archive.zip'

            filenames = ['pack1/app.py', 'pack1/utils.py',
                         'pack1/subpackage/code.py', 'pack2/code.py']
            in_archive_filenames = ['python/lib/python3.7/site-packages/' + f for f in filenames]
            ignored_filenames = ['static/abc.js', 'pack3/py.py']
            in_archive_ignored = [
                'python/lib/python3.7/site-packages/' + f for f in ignored_filenames]
            _create_files(workdir, filenames + ignored_filenames)

            packaging.create_project_archive(archive_path, workdir, ['pack1', 'pack2'])

            self.assertTrue(archive_path.is_file(), f'{archive_path} is not a file')
            zip = zipfile.ZipFile(archive_path)

            files_in_zip = zip.namelist()
            for file in in_archive_filenames:
                self.assertIn(file, files_in_zip)
            for ignored in in_archive_ignored:
                self.assertNotIn(ignored, files_in_zip)


def _is_name_in_zip(name: str, zip_file: zipfile.ZipFile) -> bool:
    return name in zip_file.namelist()


def _create_files(root: Path, files: [str]):
    for file in files:
        filepath = Path(file)
        os.makedirs(root / filepath.parent, exist_ok=True)
        (root / filepath).touch()
