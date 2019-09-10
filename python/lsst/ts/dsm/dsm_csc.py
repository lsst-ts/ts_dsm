import asyncio
import csv
import logging
import os
import pathlib
import tempfile
import yaml

import aionotify

from lsst.ts import salobj

from . import utils

__all__ = ['DSMCSC']


class DSMCSC(salobj.ConfigurableCsc):
    """
    Commandable SAL Component to interface with the LSST DSMs.
    """

    def __init__(self, index, config_dir=None, initial_state=salobj.State.STANDBY,
                 initial_simulation_mode=0):
        """
        Initialize DSM CSC.

        Parameters
        ----------
        index : `int`
            Index for the DSM. This enables the control of multiple DSMs.
        config_dir : `str`, optional
            The location of the CSC configuration files.
        initial_state : `lsst.ts.salobj.State`, optional
            State to place CSC in after initialization.
        initial_simulation_mode : `int`, optional
            Flag to determine mode of operation.
        """
        schema_path = pathlib.Path(__file__).resolve().parents[4].joinpath("schema", "DSM.yaml")

        self.telemetry_directory = None
        # self.telemetry_loop_running = False
        self.telemetry_loop_task = salobj.make_done_future()
        self.telemetry_watcher = aionotify.Watcher()
        self.simulated_telemetry_ui_config_written = False
        # self.simulated_telemetry_loop_running = False
        self.simulated_telemetry_loop_task = salobj.make_done_future()
        self.simulation_loop_time = None
        self.config = None

        # self.loop_die_timeout = 5  # how long to wait for the loops to die?

        super().__init__("DSM", index, schema_path=schema_path, config_dir=config_dir,
                         initial_state=initial_state,
                         initial_simulation_mode=initial_simulation_mode)

        ch = logging.StreamHandler()
        self.log.addHandler(ch)

    # async def begin_exitControl(self, id_data):
    #     """Begin do_exitControl; called after state changes but before
    # command
    #        acknowledged.

    #     This method will remove the telemetry directory if in simulation
    # mode.

    #     Parameters
    #     ----------
    #     id_data : `CommandIdData`
    #         Command ID and data
    #     """
    #     if self.simulation_mode:
    #         if os.path.exists(self.telemetry_directory):
    #             os.removedirs(self.telemetry_directory)

    # async def begin_standby(self, id_data):
    #     """Begin do_standby; called after state changes but before command
    #        acknowledged.

    #     This method will stop the telemetry and if necessary the simulation
    #     loops.

    #     Parameters
    #     ----------
    #     id_data : `CommandIdData`
    #         Command ID and data
    #     """
    #     self.simulated_telemetry_loop_running = False
    #     self.telemetry_loop_running = False

    # async def begin_start(self, id_data):
    #     """Begin do_start; called after state changes but before command
    #        acknowledged.

    #     This method will create the telemetry directory if in simulation mode
    #     and the directory has not been specified previously.

    #     Parameters
    #     ----------
    #     id_data : `CommandIdData`
    #         Command ID and data
    #     """
    #     if self.simulation_mode and self.telemetry_directory is None:
    #         self.telemetry_directory = tempfile.mkdtemp()
    #         self.log.debug(f"Creating temporary directory:
    # {self.telemetry_directory}")

    #     await super().begin_start(id_data)

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
        if self.simulation_mode:
            if os.path.exists(self.telemetry_directory):
                os.removedirs(self.telemetry_directory)

        await super().close_tasks()

    async def configure(self, config):
        """Send settingsApplied messages.

        Parameters
        ----------
        config : `types.SimpleNamespace`
            The current configuration.
        """
        self.config = config
        self.simulation_loop_time = self.config.simulation_loop_time
        if self.config.telemetry_directory != "None":
            self.telemetry_directory = self.config.telemetry_directory

        self.evt_settingsApplied.set_put(telemetryDirectory=self.telemetry_directory,
                                         simulationLoopTime=self.simulation_loop_time)

    # async def do_standby(self, id_data):
    #     """Transition to from `State.DISABLED` to `State.STANDBY`.

    #     After switching from disable to standby, wait for telemetry and if
    #     necessary simulation loops to finish. If they take longer then a
    #     timeout to finish, cancel the future.

    #     Parameters
    #     ----------
    #     id_data : `CommandIdData`
    #         Command ID and data
    #     """
    #     await super().do_standby(id_data)

    #     if self.simulation_mode:
    #         self.log.info("Shutting down simulated telemetry loop.")
    #         await self.wait_loop(self.simulated_telemetry_loop_task)
    #         self.simulated_telemetry_ui_config_written = False

    #     self.log.info("Shutting down telemetry loop.")
    #     await self.wait_loop(self.telemetry_task)

    async def do_start(self, id_data):
        """Transition to from `State.STANDBY` to `State.DISABLED`.

        After switching from standby to disable, start the telemetry watching.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """

        self.log.info(f"Telemetry dir: {self.telemetry_directory}")
        try:
            self.telemetry_watcher.watch(path=self.telemetry_directory, flags=aionotify.Flags.CLOSE_WRITE)
            loop = asyncio.get_running_loop()
            await self.telemetry_watcher.setup(loop)
        except ValueError:
            # Watch already running
            pass

        await super().do_start(id_data)
        # self.telemetry_task = asyncio.ensure_future(self.telemetry_loop())

    # async def end_standby(self, id_data):
    #     """End do_standby; called after state changes but before command
    #        acknowledged.

    #     This method will clean up the simulation files if necessary.

    #     Parameters
    #     ----------
    #     id_data : `CommandIdData`
    #         Command ID and data
    #     """
    #     if self.simulation_mode:
    #         self.log.info("Cleanup simulation files.")
    #         self.cleanup_simulation()

    # async def end_start(self, id_data):
    #     """End do_start; called after state changes but before command
    #        acknowledged.

    #     This method will start the telemetry and if necessary the simulation
    #     loops.

    #     Parameters
    #     ----------
    #     id_data : `CommandIdData`
    #         Command ID and data
    #     """
    #     self.log.debug("Finishing start command.")
    #     if self.simulation_mode:
    #         self.simulated_telemetry_loop_task =
    # asyncio.ensure_future(self.simulated_telemetry_loop())

    @staticmethod
    def get_config_pkg():
        """Provide the configuration repository / directory.

        Returns
        -------
        `str`
            The configuration repository / directory.
        """
        return "ts_config_eas"

    async def implement_simulation_mode(self, simulation_mode):
        """Setup items related to simulation mode.

        Parameters
        ----------
        simulation_mode : `int`
            Constant that declares simulation mode or not.

        Raises
        ------
        `lsst.ts.salobj.ExpectedError`
            Warns user if correct simulation mode value is not provided.
        """
        if simulation_mode not in (0, 1):
            raise salobj.ExpectedError(f"Simulation_mode={simulation_mode} must be 0 or 1")

        if self.simulation_mode == simulation_mode:
            return

    def process_dat_file(self, ifile):
        """Process the dome seeing DAT file and send telemetry.

        Parameters
        ----------
        ifile : `str`
          The filename to read and process.
        """
        self.log.info(f"Process {ifile} file.")
        with open(os.path.join(self.telemetry_directory, ifile), 'r') as infile:
            self.log.debug("Telemetry file opened.")
            reader = csv.reader(infile)
            for row in reader:
                try:
                    self.log.debug(f"Row: {row}")
                    self.tel_domeSeeing.set_put(dsmIndex=self.salinfo.index,
                                                timestampCurrent=utils.convert_time(row[0]),
                                                timestampFirstMeasurement=utils.convert_time(row[1]),
                                                timestampLastMeasurement=utils.convert_time(row[2]),
                                                rmsX=float(row[3]),
                                                rmsY=float(row[4]))
                    self.log.debug("Done row.")
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
        with open(os.path.join(self.telemetry_directory, ifile), 'r') as infile:
            self.log.debug("UI Config file opened.")
            content = yaml.safe_load(infile)
            ui_config_file = pathlib.PosixPath(content['ui_versions']['config_file']).as_uri()
            self.tel_configuration.set_put(dsmIndex=self.salinfo.index,
                                           timestampConfigStart=utils.convert_time(content['timestamp']),
                                           uiVersionCode=content['ui_versions']['code'],
                                           uiVersionConfig=content['ui_versions']['config'],
                                           uiConfigFile=ui_config_file,
                                           cameraName=content['camera']['name'],
                                           cameraFps=content['camera']['fps'],
                                           dataBufferSize=content['data']['buffer_size'],
                                           dataAcquisitionTime=content['data']['acquisition_time'])
            self.log.info("Done with UI config file.")

    def report_summary_state(self):
        """Handle things that depend on state.
        """
        self.log.info(f"Current state: {self.summary_state}")
        if self.summary_state in (salobj.State.DISABLED, salobj.State.ENABLED):
            if self.telemetry_loop_task.done():
                self.log.info("Adding telemetry loop task.")
                self.telemetry_loop_task = asyncio.ensure_future(self.telemetry_loop())

            if self.simulation_mode and self.simulated_telemetry_loop_task.done():
                self.log.info("Adding simulated telemetry loop task.")
                self.simulated_telemetry_loop_task = asyncio.ensure_future(self.simulated_telemetry_loop())
        else:
            if self.simulation_mode and self.telemetry_directory is None:
                self.telemetry_directory = tempfile.mkdtemp()
                self.log.info(f"Creating temporary directory: {self.telemetry_directory}")

            if self.simulation_mode and not self.simulated_telemetry_loop_task.done():
                self.log.info("Shutting down simulated telemetry loop.")
                self.simulated_telemetry_loop_task.cancel()
                self.simulated_telemetry_ui_config_written = False

                self.log.info("Cleanup simulation files.")
                self.cleanup_simulation()

            if not self.telemetry_loop_task.done():
                self.log.info("Shutting down telemetry loop.")
                self.telemetry_loop_task.cancel()

        super().report_summary_state()

    async def simulated_telemetry_loop(self):
        """Run the simulated telemetry loop.
        """
        # if not self.simulated_telemetry_loop_task.done():
        #     raise IOError('Simulated telemetry loop still running...')
        # self.simulated_telemetry_loop_running = True

        while True:
            if not self.simulated_telemetry_ui_config_written:
                utils.create_telemetry_config(self.telemetry_directory)
                self.log.debug('Writing simulated UI configuration file.')
                self.simulated_telemetry_ui_config_written = True

            utils.create_telemetry_data(self.telemetry_directory)
            self.log.debug('Writing simulated telemetry data file.')

            await asyncio.sleep(self.simulation_loop_time)

    async def telemetry_loop(self):
        """Run the telemetry loop.
        """
        # if not self.telemetry_loop_task.done():
        #     raise IOError('Telemetry loop still running...')
        # self.telemetry_loop_running = True

        while True:
            ioevent = await self.telemetry_watcher.get_event()
            self.process_event(ioevent)

    # async def wait_loop(self, loop):
    #     """A utility method to wait for a task to die or cancel it and handle
    #        the aftermath.

    #     Parameters
    #     ----------
    #     loop : _asyncio.Future
    #     """
    #     # wait for telemetry loop to die or kill it if timeout
    #     timeout = True
    #     for i in range(self.loop_die_timeout):
    #         if loop.done():
    #             timeout = False
    #             break
    #         await asyncio.sleep(salobj.base_csc.HEARTBEAT_INTERVAL)
    #     if timeout:
    #         loop.cancel()
    #     try:
    #         await loop
    #         self.log.info("Loop shutdown.")
    #     except asyncio.CancelledError:
    #         self.log.info('Loop cancelled...')
    #     except Exception as e:
    #         # Something else may have happened. I still want to disable
    #         # as this will stop the loop on the target production
    #         self.log.exception(e)
