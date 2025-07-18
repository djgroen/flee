#!/usr/bin/env python

"""The setup script."""

import pathlib
import os
#import pkg_resources
from setuptools import setup, find_packages
import versioneer


pkg_local_dir = os.path.dirname(os.path.abspath(__file__))

with open(
        os.path.join(pkg_local_dir, "README.md"),
        encoding='utf-8'
) as readme_file:
    long_description = readme_file.read()


#with pathlib.Path("requirements.txt").open() as requirements_txt:
#    install_requires = [
#        str(requirement)
#        for requirement
#        in pkg_resources.parse_requirements(requirements_txt)
#    ]

test_requirements = ["pytest>=3", ]

cmdclass = versioneer.get_cmdclass()

setup(
    author="Derek Groen",
    author_email="Derek.Groen@brunel.ac.uk",
    python_requires=">=3.8",
    classifiers=[
        # list of classifiers -> https://pypi.org/classifiers/
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    description="Flee is an agent-based modelling toolkit which is "
    "purpose-built for simulating the movement of individuals "
    "across geographical locations.",
    install_requires=install_requires,
    license="BSD-3-Clause",
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords="flee",
    name="flee",
    packages=find_packages(include=["flee", "flee.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://flee.readthedocs.io",
    version=versioneer.get_version(),
    cmdclass=cmdclass,
    zip_safe=False,
    )
