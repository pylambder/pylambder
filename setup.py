"""A setuptools based setup module, based on
[this example](https://github.com/pypa/sampleproject/blob/master/setup.py)

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
import os
from os import path

here = path.abspath(path.dirname(__file__))

with open('pylambder/__init__.py', 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break
    else:
        raise RuntimeError("Version information missing")

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def files_in_dir(relative_to, directory):
    result = []
    for dirpath, _subdirs, files in os.walk(path.join(relative_to, directory)):
        result += [path.relpath(path.join(dirpath, f), relative_to) for f in files]
    return result

setup(
    name='pylambder',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,  # Required

    description='Remote task execution on AWS Lambda for Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # url='https://github.com/pypa/sampleproject',  # Optional
    author='Wojciech Geisler, Artur Jopek',  # Optional
    author_email='wojciech.geisler@gmail.com',  # Optional

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',
        'Topic :: System :: Distributed Computing',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],

    # Note that this is a string of words separated by whitespace, not a list.
    keywords='task aws lambda',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  # Required

    # Specify which Python versions you support. In contrast to the
    # 'Programming Language' classifiers above, 'pip install' will check this
    # and refuse to install the project if the version does not match. If you
    # do not support Python 2, you can simplify this to '>=3.5' or similar, see
    # https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
    python_requires='>= 3.7, <4',

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'boto3>=1.9.210',
        'websockets>=8,<10',
        'janus==0.4.0',
    ],  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    extras_require={  # Optional
        'dev': ['pylint'],
        'test': [],
    },

    package_data={
        'pylambder': files_in_dir('pylambder', 'sam-data') + \
            files_in_dir('pylambder', 'packaged')
    },

    entry_points={
        'console_scripts': [
            'pylambder=pylambder.cli:main'
        ]
    }
)
