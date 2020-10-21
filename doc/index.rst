.. |Michael Reuter| replace::  *mareuter@lsst.org*
.. |Brian Stalder| replace:: *bstalder@lsst.org*

#########################
DSM
#########################

.. image:: https://img.shields.io/badge/SAL-API-gray.svg
    :target: https://ts-xml.lsst.io/sal_interfaces/DSM.html
.. image:: https://img.shields.io/badge/GitHub-gray.svg
    :target: https://github.com/lsst-ts/ts_dsm
.. image:: https://img.shields.io/badge/Jira-gray.svg
    :target: https://jira.lsstcorp.org/issues/?jql=labels+%3D+ts_dsm
.. image:: https://img.shields.io/badge/Jenkins-gray.svg
    :target: https://tssw-ci.lsst.org/job/LSST_Telescope-and-Site/job/ts_dsm/

.. _Overview:

Overview
========

The Dome Seeing Monitor (DSM) CSC is responsible for taking output telemetry
files from the Dome Seeing Monitor UI and sending the information via SAL
for recording in the EFD. Although the DSM is part of the Environmental Awareness
System, it currently runs stand-alone and is not tied in to the EAS in any manner.

As with all CSCs, information on the package, developers and product owners can be found in the `Master CSC Table <ts_xml:index:master-csc-table:DSM>`_.

.. note:: If you are interested in viewing other branches of this repository append a `/v` to the end of the url link. For example `https://ts_dsm.lsst.io/v/`


.. _User_Documentation:

User Documentation
==================

User-level documentation, found at the link below, is aimed at personnel looking to perform the standard use-cases/operations with the DSM.

.. toctree::
    user-guide/user-guide
    :maxdepth: 2

.. _Configuration:

Configuring the DSM
=========================================

The DSM is a non-configurable CSC.

.. _Development_Documentation:

Development Documentation
=========================

This area of documentation focuses on the classes used, API's, and how to participate to the development of the DSM software packages.

.. toctree::
    developer-guide/developer-guide
    :maxdepth: 1

.. _Version_History:

Version History
===============

The version history of the DSM is found at the following link.

.. toctree::
    version-history
    :maxdepth: 1
