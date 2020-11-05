"""Sphinx configuration file for TSSW package"""

from documenteer.sphinxconfig.stackconf import build_package_configs
import lsst.ts.dsm


_g = globals()
_g.update(build_package_configs(project_name="ts_dsm", version=lsst.ts.dsm.__version__))

intersphinx_mapping["ts_xml"] = ("https://ts-xml.lsst.io", None)  # noqa
intersphinx_mapping["ts_salobj"] = ("https://ts-salobj.lsst.io", None)  # noqa
