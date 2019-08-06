import unittest
import asyncio
import numpy as np
import os

from lsst.ts import salobj

from lsst.ts.dsm import dsm_csc

np.random.seed(47)

index_gen = salobj.index_generator()

LONG_TIMEOUT = 20  # timeout for starting SAL components (sec)


class Harness:
    def __init__(self, initial_state):
        salobj.test_utils.set_random_lsst_dds_domain()
        self.index = 1
        self.csc = dsm_csc.DSMCSC(index=self.index, initial_state=initial_state,
                                  initial_simulation_mode=1)
        self.remote = salobj.Remote(domain=self.csc.domain, name="DSM", index=self.index)

    async def __aenter__(self):
        await self.csc.start_task
        await self.remote.start_task
        return self

    async def __aexit__(self, *args):
        await self.csc.close()


class TestDSMCSC(unittest.TestCase):

    def cleanup(self, directory):
        """Cleanup telemetry directory if tests fail.
        """
        if os.path.exists(directory):
            for tfile in os.listdir(directory):
                os.remove(os.path.join(directory, tfile))
            os.removedirs(directory)

    def test_lifecycle_behavior(self):
        """Test that the DSM through the standard lifecycle.

        The emphasis for this test is making sure the telemetry loop can be
        started and stopped through the lifecycle commands.
        """
        async def doit():
            async with Harness(initial_state=salobj.State.STANDBY) as harness:
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.STANDBY)
                self.assertEqual(harness.csc.simulation_mode, 1)
                self.assertIsNotNone(harness.csc.telemetry_directory)
                self.assertTrue(os.path.exists(harness.csc.telemetry_directory))

                self.cleanup(harness.csc.telemetry_directory)

        asyncio.get_event_loop().run_until_complete(doit())


if __name__ == '__main__':
    unittest.main()
