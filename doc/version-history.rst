===============
Version History
===============

v2.6.1
------

 * Fix flaky unit test

v2.6.0
------

 * Remove ts-idl conda dependency and replace with ts-xml
 * Change deprecated test call
 * Update unit tests for better stability

v2.5.4
------

 * Update ts-conda-build pin to 0.4 in conda meta.yaml
 * Update to latest pre-commit configuration

v2.5.3
------

* Remove ts-dds from conda meta.yaml

v2.5.2
------

* Remove script_env section and add Python generalizer to script section in conda meta.yaml

v2.5.1
------

* Change to standard pre-commit configuration
* Update conda meta.yaml for new specs
* Fix conda package dependencies

v2.5.0
------

* Support for new setuptool packaging
* Runner scripts no longer need .py extension

v2.4.0
------

* Support for salobj 7

v2.3.0
------

* Switch to `asyncinotify <https://asyncinotify.readthedocs.io/>`_ for file system watcher

v2.2.2
------

* Remove simulation file after message sent
* Remove pytest-runner from conda build

v2.2.1
------
* Update code to new black version
* Pin conda builder version
* Update pre-commit hook versions
* Fix documentation build issue
* Update unit tests to new base class
* Fix internal simulation mode variable
* Set version class variable to silence warning
* Disable test due to salobj issue

v2.2.0
------
* Allow command-line state transitioning for CSC
* Update documentation to reflect new functionality
* Convert to new pre-commit methodology

v2.1.0
------
* Convert configuration message from telemetry to event

v2.0.0
------
* Update to SALOBJ6 including upcoming deprecations
* Convert back to non-configurable CSC
* Add CSC documentation

v1.1.2
------
* Update conda package building

v1.1.1
------
* Address minor issues

v1.1.0
------
* Update to SALOBJ5 code base

v1.0.0
------
* Fully functional version
