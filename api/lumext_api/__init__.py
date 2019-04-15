"""LUMEXT for vCloud Director

.. moduleauthor:: Ludovic Rivallain <ludovic.rivallain@gmail.com>

"""
# Standard imports
import sys

# Test python version
if sys.version_info < (3, 6):
    raise Exception('LUMExt for vCloud Director requires Python versions >=3.6.')

# Declare submodules
__all__ = [
    "utils",
    "ldap_manager",
    "lumext"
]
