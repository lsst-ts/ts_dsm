from importlib import metadata

import setuptools
import setuptools_scm

scm_version = metadata.version("setuptools_scm")

setuptools.setup(
    version=setuptools_scm.get_version(write_to="python/lsst/ts/dsm/version.py")
)
