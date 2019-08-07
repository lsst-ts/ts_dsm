import asyncio
import logging
import os
import tempfile

from lsst.ts import salobj

from lsst.ts.dsm import create_telemetry_config, create_telemetry_data

__all__ = ['DSMCSC']

SIMULATION_LOOP_SLEEP = 1  # seconds


class DSMCSC(salobj.BaseCsc):
    """
    Commandable SAL Component to interface with the LSST DSMs.
    """

    def __init__(self, index, initial_state, initial_simulation_mode=0):
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
        self.simulated_telemetry_ui_config_written = False
        self.simulated_telemetry_loop_running = False
        self.simulated_telemetry_task = None

        self.loop_die_timeout = 5  # how long to wait for the loops to die?

        super().__init__("DSM", index, initial_state=initial_state,
                         initial_simulation_mode=initial_simulation_mode)

        ch = logging.StreamHandler()
        self.log.addHandler(ch)

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

    def cleanup_simulation(self):
        """Remove all generated files and directory from simulation
        """
        if os.path.exists(self.telemetry_directory):
            for tfile in os.listdir(self.telemetry_directory):
                os.remove(os.path.join(self.telemetry_directory, tfile))
        os.removedirs(self.telemetry_directory)

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
            await self.wait_loop(self.simulated_telemetry_task)

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
        if self.simulation_mode:
            self.simulated_telemetry_task = asyncio.ensure_future(self.simulated_telemetry_loop())

    async def implement_simulation_mode(self, simulation_mode):
        """Setup items related to simulation mode.

        Parameters
        ----------
        simulation_mode : int
            Constant that declares simulation mode or not.
        """
        if simulation_mode:
            self.telemetry_directory = tempfile.mkdtemp()
            self.log.info(f"Creating temporary directory: {self.telemetry_directory}")

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
        except asyncio.CancelledError:
            self.log.info('Loop cancelled...')
        except Exception as e:
            # Something else may have happened. I still want to disable as this
            # will stop the loop on the target production
            self.log.exception(e)
