.. |Michael Reuter| replace::  *mareuter@lsst.org*
.. |Brian Stalder| replace:: *bstalder@lsst.org*

.. _User_Guide:

#######################
DSM User Guide
#######################

.. Update links and labels below
.. image:: https://img.shields.io/badge/GitHub-ts_dsm-green.svg
    :target: https://github.com/lsst-ts/ts_dsm
.. image:: https://img.shields.io/badge/Jenkins-ts_dsm-green.svg
    :target: https://tssw-ci.lsst.org/job/LSST_Telescope-and-Site/job/ts_dsm/
.. image:: https://img.shields.io/badge/Jira-ts_dsm-green.svg
    :target: https://jira.lsstcorp.org/issues/?jql=labels+%3D+ts_dsm
.. image:: https://img.shields.io/badge/ts_xml-DSM-green.svg
    :target: https://ts-xml.lsst.io/sal_interfaces/DSM.html

The DSM CSC is a support CSC that is used in conjunction with the DSM UI in order
to produce seeing measurements along the DSM probes line of sight. The functionality to produce these measurements are contained within the UI and are not described in this
document. The UI is also responsible for the interaction with the DSM probe hardware. 
The operational interaction of these systems and other details are captured in `SITCOMTN-001 <https://sitcomtn-001.lsst.io/>`_ technical note.

DSM Interface
======================

The DSM XML interface definition can be found 
`here <https://ts-xml.lsst.io/sal_interfaces/DSM.html>`_. The CSC accepts all of the 
standard state transition commands except ``enterControl``. No other CSC commands are provided. The CSC also provides all of the standard events required by the system. 
Those events associated with a configurable CSC are not provided since the DSM CSC
is not configurable. One event of particular note is ``simulationMode``. This will
allow one to determine the mode the CSC is being run. 

The telemetry provided by the CSC consists of two topics: ``configuration`` and
``domeSeeing``. The ``configuration`` topic handles passing along the current configuration
of the DSM UI to the system. The ``domeSeeing`` topic provides the calculated values provided by the DSM UI. They are measures of the seeing in the DSMs laser line of sight.
 
Example Use-Case
================

See the techincal note listed above for operational descriptions.
