import unittest
from unittest.mock import patch
import os
import zipfile
import tempfile

import pylambder.packaging.packaging as packaging


class TestPackaging(unittest.TestCase):

    def test_archive_creation(self):
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
                archive_path = os.path.join(dir, "archive")
                archive_path_with_ext = archive_path + ".zip"
                deps = ["somepackage", "otherpackage"]
                packaging.create_packages_archive(archive_path, deps)

                self.assertTrue(os.path.isfile(archive_path_with_ext))

                zip = zipfile.ZipFile(archive_path_with_ext)

                self.assertTrue(_is_name_in_zip(
                    "python/lib/python3.7/site-packages/somepackage/", zip))
                self.assertTrue(_is_name_in_zip(
                    "python/lib/python3.7/site-packages/somepackage/stub", zip))
                self.assertTrue(_is_name_in_zip(
                    "python/lib/python3.7/site-packages/otherpackage/", zip))
                self.assertTrue(_is_name_in_zip(
                    "python/lib/python3.7/site-packages/otherpackage/stub", zip))


def _is_name_in_zip(name: str, zip_file: zipfile.ZipFile) -> bool:
    return name in zip_file.namelist()
