from distutils.core import setup
import setuptools

long_description = """LDAP user management extension for vCloud Director >=9.1

LUMext is a vCD UI & API extension to manage LDAP-based organisation's users and groups through *VMware vCloud Director*.

This extension aims to provide a way to share a single LDAP server for multiple organisations to simplify the user management.
"""

setup(
    name='lumext_api',
    version='0.1',
    author="Ludovic Rivallain, Camille Kessab",
    author_email='ludovic.rivallain@gmail.com',
    packages=setuptools.find_packages(),
    description="LUMext is a vCD UI & API extension to manage LDAP-based organisation's users through vCD.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "VcdExtMessageWorker",
        "coloredlogs",
        "pyyaml",
        "python-ldap",
        "simplejson",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'lumext=lumext_api.__main__:main',
        ],
    })
