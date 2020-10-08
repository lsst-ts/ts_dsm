..
  This is a template for the user-guide documentation that will accompany each CSC.
  This template is provided to ensure that the documentation remains similar in look, feel, and contents to users.
  The headings below are expected to be present for all CSCs, but for many CSCs, additional fields will be required.

  ** All text in square brackets [] must be re-populated accordingly **

  See https://developer.lsst.io/restructuredtext/style.html
  for a guide to reStructuredText writing.

  Use the following syntax for sections:

  Sections
  ========

  and

  Subsections
  -----------

  and

  Subsubsections
  ^^^^^^^^^^^^^^

  To add images, add the image file (png, svg or jpeg preferred) to the
  images/ directory. The reST syntax for adding the image is

  .. figure:: /images/filename.ext
   :name: fig-label

   Caption text.

  Feel free to delete this instructional comment.

.. Fill out data so contacts section below is auto-populated
.. add name and email between the *'s below e.g. *Marie Smith <msmith@lsst.org>*
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
