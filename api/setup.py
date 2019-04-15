from distutils.core import setup
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

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
        "python-json-config",
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
