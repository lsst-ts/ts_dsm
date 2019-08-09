import aionotify
import asyncio
import csv
import logging
import os
import tempfile
import yaml

from lsst.ts import salobj

from lsst.ts.dsm import convert_time, create_telemetry_config, create_telemetry_data

__all__ = ['DSMCSC']

SIMULATION_LOOP_SLEEP = 1  # seconds


class DSMCSC(salobj.BaseCsc):
    """
    Commandable SAL Component to interface with the LSST DSMs.
    """

    def __init__(self, index, initial_state=salobj.State.STANDBY, initial_simulation_mode=0):
        """
        Initialize DSM CSC.

        Parameters
        ----------
        index : int
            Index for the DSM. This enables the control of multiple DSMs.
        """
        self.telemetry_directory = None
        self.telemetry_loop_running = False
        self.telemetry_loop_task = None
        self.telemetry_watcher = aionotify.Watcher()
        self.simulated_telemetry_ui_config_written = False
        self.simulated_telemetry_loop_running = False
        self.simulated_telemetry_task = None

        self.loop_die_timeout = 5  # how long to wait for the loops to die?

        super().__init__("DSM", index, initial_state=initial_state,
                         initial_simulation_mode=initial_simulation_mode)

        ch = logging.StreamHandler()
        self.log.addHandler(ch)

    async def begin_exitControl(self, id_data):
        """Begin do_exitControl; called after state changes but before command
           acknowledged.

        This method will remove the telemetry directory if in simulation mode.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """
        if self.simulation_mode:
            if os.path.exists(self.telemetry_directory):
                os.removedirs(self.telemetry_directory)

    async def begin_standby(self, id_data):
        """Begin do_standby; called after state changes but before command
           acknowledged.

        This method will stop the telemetry and if necessary the simulation
        loops.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """
        self.simulated_telemetry_loop_running = False
        self.telemetry_loop_running = False

    async def begin_start(self, id_data):
        """Begin do_start; called after state changes but before command
           acknowledged.

        This method will create the telemetry directory if in simulation mode
        and the directory has not been specified previously.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """
        if self.simulation_mode and self.telemetry_directory is None:
            self.telemetry_directory = tempfile.mkdtemp()
            self.log.info(f"Creating temporary directory: {self.telemetry_directory}")

    def cleanup_simulation(self):
        """Remove all generated files and directory from simulation
        """
        if os.path.exists(self.telemetry_directory):
            for tfile in os.listdir(self.telemetry_directory):
                os.remove(os.path.join(self.telemetry_directory, tfile))

    async def do_standby(self, id_data):
        """Transition to from `State.DISABLED` to `State.STANDBY`.

        After switching from disable to standby, wait for telemetry and if
        necessary simulation loops to finish. If they take longer then a
        timeout to finish, cancel the future.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """
        await super().do_standby(id_data)

        if self.simulation_mode:
            self.log.info("Shutting down simulated telemetry loop.")
            await self.wait_loop(self.simulated_telemetry_task)
            self.simulated_telemetry_ui_config_written = False

        self.log.info("Shutting down telemetry loop.")
        await self.wait_loop(self.telemetry_task)

    async def do_start(self, id_data):
        """Transition to from `State.STANDBY` to `State.DISABLED`.

        After switching from standby to disable, start the telemetry watching.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """
        await super().do_start(id_data)
        try:
            self.telemetry_watcher.watch(path=self.telemetry_directory, flags=aionotify.Flags.CLOSE_WRITE)
            loop = asyncio.get_running_loop()
            await self.telemetry_watcher.setup(loop)
        except ValueError:
            # Watch already running
            pass

        self.telemetry_task = asyncio.ensure_future(self.telemetry_loop())

    async def end_standby(self, id_data):
        """End do_standby; called after state changes but before command
           acknowledged.

        This method will clean up the simulation files if necessary.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """
        if self.simulation_mode:
            self.log.info("Cleanup simulation files.")
            self.cleanup_simulation()

    async def end_start(self, id_data):
        """End do_start; called after state changes but before command
           acknowledged.

        This method will start the telemetry and if necessary the simulation
        loops.

        Parameters
        ----------
        id_data : `CommandIdData`
            Command ID and data
        """
        self.log.info("Finishing start command.")
        if self.simulation_mode:
            self.simulated_telemetry_task = asyncio.ensure_future(self.simulated_telemetry_loop())

    async def implement_simulation_mode(self, simulation_mode):
        """Setup items related to simulation mode.

        Parameters
        ----------
        simulation_mode : int
            Constant that declares simulation mode or not.
        """
        self.log.info("Simluation mode possible.")
        pass

    def process_dat_file(self, ifile):
        """Process the dome seeing DAT file and send telemetry.

        Parameters
        ----------
        ifile : str
          The filename to read and process.
        """
        self.log.info(f"Process {ifile} file.")
        with open(os.path.join(self.telemetry_directory, ifile), 'r') as infile:
            self.log.info("Telemetry file opened.")
            reader = csv.reader(infile)
            for row in reader:
                self.log.info(f"Row: {row}")
                self.tel_domeSeeing.set_put(dsmIndex=self.salinfo.index,
                                            timestampCurrent=convert_time(row[0]),
                                            timestampFirstMeasurement=convert_time(row[1]),
                                            timestampLastMeasurement=convert_time(row[2]),
                                            rmsX=float(row[3]),
                                            rmsY=float(row[4]))
                self.log.info("Done row.")

    def process_event(self, event):
        """Process I/O Events.

        Parameters
        ----------
        event : `aionotify.Event`
            Payload containing the I/O event information.
        """
        self.log.info(f"Event: Flags = {event.flags}, Name = {event.name}")
        if event.flags & aionotify.Flags.CLOSE_WRITE:
            if event.name.endswith("yaml"):
                self.process_yaml_file(event.name)
            if event.name.endswith("dat"):
                self.process_dat_file(event.name)

    def process_yaml_file(self, ifile):
        """Process the UI configuration YAML file and send telemetry.

        Parameters
        ----------
        ifile : str
          The filename to read and process.
        """
        self.log.info(f"Process {ifile} file.")
        with open(os.path.join(self.telemetry_directory, ifile), 'r') as infile:
            self.log.info("UI Config file opened.")
            content = yaml.safe_load(infile)
            self.tel_configuration.set_put(dsmIndex=self.salinfo.index,
                                           uiVersionCode=content['ui_versions']['code'],
                                           uiVersionConfig=content['ui_versions']['config'],
                                           cameraName=content['camera']['name'],
                                           cameraFps=content['camera']['fps'],
                                           dataBufferSize=content['data']['buffer_size'],
                                           dataAcquisitionTime=content['data']['acquisition_time'])
            self.log.info("Done with UI config file.")

    async def simulated_telemetry_loop(self):
        """Run the simulated telemetry loop.
        """
        if self.simulated_telemetry_loop_running:
            raise IOError('Simulated telemetry loop still running...')
        self.simulated_telemetry_loop_running = True

        while self.simulated_telemetry_loop_running:
            if not self.simulated_telemetry_ui_config_written:
                create_telemetry_config(self.telemetry_directory)
                self.log.info('Writing simulated UI configuration file.')
                self.simulated_telemetry_ui_config_written = True

            create_telemetry_data(self.telemetry_directory)
            self.log.info('Writing simulated telemetry data file.')

            await asyncio.sleep(SIMULATION_LOOP_SLEEP)

    async def telemetry_loop(self):
        """Run the telemetry loop.
        """
        if self.telemetry_loop_running:
            raise IOError('Telemetry loop still running...')
        self.telemetry_loop_running = True

        while self.telemetry_loop_running:
            ioevent = await self.telemetry_watcher.get_event()
            self.process_event(ioevent)

    async def wait_loop(self, loop):
        """A utility method to wait for a task to die or cancel it and handle
           the aftermath.

        Parameters
        ----------
        loop : _asyncio.Future
        """
        # wait for telemetry loop to die or kill it if timeout
        timeout = True
        for i in range(self.loop_die_timeout):
            if loop.done():
                timeout = False
                break
            await asyncio.sleep(salobj.base_csc.HEARTBEAT_INTERVAL)
        if timeout:
            loop.cancel()
        try:
            await loop
            self.log.info("Loop shutdown.")
        except asyncio.CancelledError:
            self.log.info('Loop cancelled...')
        except Exception as e:
            # Something else may have happened. I still want to disable as this
            # will stop the loop on the target production
            self.log.exception(e)
