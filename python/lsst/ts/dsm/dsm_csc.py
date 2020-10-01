import asyncio
import csv
import logging
import os
import pathlib
import shutil
import tempfile
import yaml

import aionotify

from lsst.ts import salobj

from . import utils
from . import version

__all__ = ["DSMCSC"]

SIMULATION_LOOP_TIMES = [0, 1, 30]  # seconds


class DSMCSC(salobj.BaseCsc):
    """
    Commandable SAL Component to interface with the LSST DSMs.
    """

    valid_simulation_modes = (0, 1, 2)

    def __init__(
        self, index, initial_state=salobj.State.STANDBY, simulation_mode=0,
    ):
        """
        Initialize DSM CSC.

        Parameters
        ----------
        index : `int`
            Index for the DSM. This enables the control of multiple DSMs.
        initial_state : `lsst.ts.salobj.State`, optional
            State to place CSC in after initialization.
        simulation_mode : `int`, optional
            Flag to determine mode of operation.
        """

        self.telemetry_directory = None
        self.telemetry_loop_task = salobj.make_done_future()
        self.telemetry_watcher = aionotify.Watcher()
        self.simulated_telemetry_ui_config_written = False
        self.simulated_telemetry_loop_task = salobj.make_done_future()
        self.simulation_loop_time = None

        super().__init__(
            "DSM", index, initial_state=initial_state, simulation_mode=simulation_mode,
        )

        ch = logging.StreamHandler()
        self.log.addHandler(ch)

        self.evt_softwareVersions.set(cscVersion=version.__version__)
        self.finish_csc_setup()

    def cleanup_simulation(self):
        """Remove all generated files and directory from simulation
        """
        if os.path.exists(self.telemetry_directory):
            for tfile in os.listdir(self.telemetry_directory):
                os.remove(os.path.join(self.telemetry_directory, tfile))

    async def close_tasks(self):
        """Clean up

        This method will remove the telemetry directory if in simulation mode.
        """
        if self._requested_simulation_mode:
            if os.path.exists(self.telemetry_directory):
                shutil.rmtree(self.telemetry_directory)

        await super().close_tasks()

    def finish_csc_setup(self):
        """Perform final setup steps for CSC.
        """
        if self._requested_simulation_mode:
            if (
                self.telemetry_directory is None
                or not self.telemetry_directory.startswith("/tmp")
            ):
                self.telemetry_directory = tempfile.mkdtemp()
                self.log.debug(
                    f"Creating temporary directory: {self.telemetry_directory}"
                )
        else:
            self.telemetry_directory = os.environ.get("DSM_TELEMETRY_DIR")
            if self.telemetry_directory is None:
                self.telemetry_directory = "/home/saluser/telemetry"

        self.simulation_loop_time = SIMULATION_LOOP_TIMES[
            self._requested_simulation_mode
        ]

    async def handle_summary_state(self):
        """Handle things that depend on state.
        """
        self.log.debug(f"Current state: {self.summary_state}")
        if self.summary_state is salobj.State.ENABLED:
            self.log.debug(f"Telemetry dir: {self.telemetry_directory}")
            try:
                self.telemetry_watcher.watch(
                    path=self.telemetry_directory, flags=aionotify.Flags.CLOSE_WRITE
                )
                loop = asyncio.get_running_loop()
                await self.telemetry_watcher.setup(loop)
            except (AssertionError, ValueError):
                # Watch already running
                pass

            if self.telemetry_loop_task.done():
                self.telemetry_loop_task = asyncio.create_task(self.telemetry_loop())

            if (
                self._requested_simulation_mode
                and self.simulated_telemetry_loop_task.done()
            ):
                self.simulated_telemetry_loop_task = asyncio.create_task(
                    self.simulated_telemetry_loop()
                )
        else:
            if self._requested_simulation_mode:
                self.simulated_telemetry_loop_task.cancel()
                self.simulated_telemetry_ui_config_written = False
                self.cleanup_simulation()

            self.telemetry_loop_task.cancel()
            if not self.telemetry_watcher.closed:
                self.telemetry_watcher.unwatch(self.telemetry_directory)
                self.telemetry_watcher.close()

    def process_dat_file(self, ifile):
        """Process the dome seeing DAT file and send telemetry.

        Parameters
        ----------
        ifile : `str`
          The filename to read and process.
        """
        self.log.info(f"Process {ifile} file.")
        with open(os.path.join(self.telemetry_directory, ifile), "r") as infile:
            reader = csv.reader(infile)
            for row in reader:
                try:
                    self.tel_domeSeeing.set_put(
                        dsmIndex=self.salinfo.index,
                        timestampCurrent=utils.convert_time(row[0]),
                        timestampFirstMeasurement=utils.convert_time(row[1]),
                        timestampLastMeasurement=utils.convert_time(row[2]),
                        rmsX=float(row[3]),
                        rmsY=float(row[4]),
                        centroidX=float(row[5]),
                        centroidY=float(row[6]),
                        flux=float(row[7]),
                        maxADC=float(row[8]),
                        fwhm=float(row[9]),
                    )
                except IndexError as error:
                    self.log.error(f"{ifile}: {error}")

    def process_event(self, event):
        """Process I/O Events.

        Parameters
        ----------
        event : `aionotify.Event`
            Payload containing the I/O event information.
        """
        self.log.debug(f"Event: Flags = {event.flags}, Name = {event.name}")
        if event.flags & aionotify.Flags.CLOSE_WRITE:
            if event.name.endswith("yaml"):
                self.process_yaml_file(event.name)
            if event.name.endswith("dat"):
                self.process_dat_file(event.name)

    def process_yaml_file(self, ifile):
        """Process the UI configuration YAML file and send telemetry.

        Parameters
        ----------
        ifile : `str`
          The filename to read and process.
        """
        self.log.info(f"Process {ifile} file.")
        with open(os.path.join(self.telemetry_directory, ifile), "r") as infile:
            content = yaml.safe_load(infile)
            ui_config_file = pathlib.PosixPath(
                content["ui_versions"]["config_file"]
            ).as_uri()
            self.tel_configuration.set_put(
                dsmIndex=self.salinfo.index,
                timestampConfigStart=utils.convert_time(content["timestamp"]),
                uiVersionCode=content["ui_versions"]["code"],
                uiVersionConfig=content["ui_versions"]["config"],
                uiConfigFile=ui_config_file,
                cameraName=content["camera"]["name"],
                cameraFps=content["camera"]["fps"],
                dataBufferSize=content["data"]["buffer_size"],
                dataAcquisitionTime=content["data"]["acquisition_time"],
            )

    async def simulated_telemetry_loop(self):
        """Run the simulated telemetry loop.
        """
        while True:
            if not self.simulated_telemetry_ui_config_written:
                utils.create_telemetry_config(
                    self.telemetry_directory, self.simulation_loop_time
                )
                self.simulated_telemetry_ui_config_written = True

            utils.create_telemetry_data(
                self.telemetry_directory, self.simulation_loop_time
            )

            await asyncio.sleep(self.simulation_loop_time)

    async def telemetry_loop(self):
        """Run the telemetry loop.
        """
        while True:
            ioevent = await self.telemetry_watcher.get_event()
            self.process_event(ioevent)
