import logging
import tempfile

from lsst.ts import salobj

__all__ = ['DSMCSC']


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
        super().__init__("DSM", index, initial_state=initial_state,
                         initial_simulation_mode=initial_simulation_mode)

        ch = logging.StreamHandler()
        self.log.addHandler(ch)

    async def implement_simulation_mode(self, simulation_mode):
        if simulation_mode:
            self.telemetry_directory = tempfile.mkdtemp()
            self.log.info(f"Creating temporary directory: {self.telemetry_directory}")
