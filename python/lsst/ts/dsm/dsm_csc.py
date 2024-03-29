import asyncio
import csv
import logging
import os
import pathlib
import shutil
import tempfile

import asyncinotify
import yaml
from lsst.ts import salobj
from lsst.ts import utils as tsUtils
from lsst.ts.dsm import __version__

from . import utils

__all__ = ["DSMCSC", "run_dsm"]

SIMULATION_LOOP_TIMES = [0, 1, 30]  # seconds

# Default telemetry directory if running in real mode and $DSM_TELEMETRY_DIR
# is not defined
DEFAULT_DSM_TELEMETRY_DIR = "/home/saluser/telemetry"


class DSMCSC(salobj.BaseCsc):
    """
    Commandable SAL Component to interface with the LSST DSMs.
    """

    enable_cmdline_state = True
    # The simulation modes fully are documented in the CSC user guide.
    valid_simulation_modes = (0, 1, 2)
    simulation_help = "0: real mode, 1: fast simulation, 2: slow simulation"
    version = __version__

    def __init__(
        self,
        index,
        initial_state=salobj.State.STANDBY,
        simulation_mode=0,
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
        self.telemetry_loop_task = tsUtils.make_done_future()
        self.telemetry_notifier = asyncinotify.Inotify()
        self.telemetry_watch = None
        self.simulated_telemetry_ui_config_written = False
        self.simulated_telemetry_loop_task = tsUtils.make_done_future()
        self.simulation_loop_time = None

        super().__init__(
            "DSM",
            index,
            initial_state=initial_state,
            simulation_mode=simulation_mode,
        )

        ch = logging.StreamHandler()
        self.log.addHandler(ch)

        self.finish_csc_setup()

    def cleanup_simulation(self):
        """Remove all generated files and directory from simulation"""
        if os.path.exists(self.telemetry_directory):
            for tfile in os.listdir(self.telemetry_directory):
                os.remove(os.path.join(self.telemetry_directory, tfile))

    async def close_tasks(self):
        """Clean up

        This method will remove the telemetry directory if in simulation mode.
        """
        if self.telemetry_watch is not None:
            self.telemetry_notifier.rm_watch(self.telemetry_watch)
            self.telemetry_watch = None
            self.telemetry_notifier.close()

        if self.simulation_mode:
            if os.path.exists(self.telemetry_directory):
                shutil.rmtree(self.telemetry_directory)

        await super().close_tasks()

    def finish_csc_setup(self):
        """Perform final setup steps for CSC."""
        if self.simulation_mode:
            if (
                self.telemetry_directory is None
                or not self.telemetry_directory.startswith("/tmp")
            ):
                self.telemetry_directory = tempfile.mkdtemp()
                self.log.debug(
                    f"Creating temporary directory: {self.telemetry_directory}"
                )
        else:
            self.telemetry_directory = os.environ.get(
                "DSM_TELEMETRY_DIR", DEFAULT_DSM_TELEMETRY_DIR
            )

        self.simulation_loop_time = SIMULATION_LOOP_TIMES[self.simulation_mode]

    async def handle_summary_state(self):
        """Handle things that depend on state."""
        self.log.debug(f"Current state: {self.summary_state}")
        if self.summary_state is salobj.State.ENABLED:
            self.log.debug(f"Telemetry dir: {self.telemetry_directory}")
            try:
                self.telemetry_watch = self.telemetry_notifier.add_watch(
                    path=self.telemetry_directory, mask=asyncinotify.Mask.CLOSE_WRITE
                )
            except (AssertionError, ValueError):
                # Watch already running
                pass

            if self.telemetry_loop_task.done():
                self.telemetry_loop_task = asyncio.create_task(self.telemetry_loop())

            if self.simulation_mode and self.simulated_telemetry_loop_task.done():
                self.simulated_telemetry_loop_task = asyncio.create_task(
                    self.simulated_telemetry_loop()
                )
        else:
            if self.simulation_mode:
                self.simulated_telemetry_loop_task.cancel()
                self.simulated_telemetry_ui_config_written = False
                self.cleanup_simulation()

            self.telemetry_loop_task.cancel()

    async def process_dat_file(self, ifile):
        """Process the dome seeing DAT file and send telemetry.

        Parameters
        ----------
        ifile : `pathlib.PosixPath`
          The filename to read and process.
        """
        self.log.info(f"Process {ifile} file.")
        with open(ifile, "r") as infile:
            reader = csv.reader(infile)
            for row in reader:
                try:
                    await self.tel_domeSeeing.set_write(
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
        if self.simulation_mode:
            os.remove(os.path.join(self.telemetry_directory, ifile))

    async def process_event(self, event):
        """Process I/O Events.

        Parameters
        ----------
        event : `asyncinotify.Event`
            Payload containing the I/O event information.
        """
        self.log.debug(f"Event: Mask = {event.mask}, Name = {event.name}")
        if event.name.suffix == ".yaml":
            await self.process_yaml_file(event.path)
        if event.name.suffix == ".dat":
            await self.process_dat_file(event.path)

    async def process_yaml_file(self, ifile):
        """Process the UI configuration YAML file and send telemetry.

        Parameters
        ----------
        ifile : `pathlib.PosixPath`
          The filename to read and process.
        """
        self.log.info(f"Process {ifile} file.")
        with open(ifile, "r") as infile:
            content = yaml.safe_load(infile)
            ui_config_file = pathlib.PosixPath(
                content["ui_versions"]["config_file"]
            ).as_uri()
            try:
                config_msg = self.evt_configuration
            except AttributeError:
                config_msg = self.tel_configuration
            await config_msg.set_write(
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
        """Run the simulated telemetry loop."""
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
        """Run the telemetry loop."""
        async for ioevent in self.telemetry_notifier:
            await self.process_event(ioevent)


def run_dsm():
    """Run the DSM CSC."""
    asyncio.run(DSMCSC.amain(index=True))
