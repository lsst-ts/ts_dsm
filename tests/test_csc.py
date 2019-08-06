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

    def tearDown(self):
        self.cleanup(self.telemetry_directory)

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
                self.telemetry_directory = harness.csc.telemetry_directory

                # Move to DISABLED state
                harness.remote.cmd_start.set(settingsToApply='simulation')
                id_ack = await harness.remote.cmd_start.start(timeout=120)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(id_ack.ack, salobj.SalRetCode.CMD_COMPLETE)
                self.assertEqual(id_ack.error, 0)
                self.assertEqual(state.summaryState, salobj.State.DISABLED)

                # Check that the simulated telemetry loop is running
                self.assertTrue(harness.csc.simulated_telemetry_loop_running)
                sim_files = len(list(os.listdir(harness.csc.telemetry_directory)))
                self.assertEqual(sim_files, 2)

                # Move to ENABLED state
                id_ack = await harness.remote.cmd_enable.start(timeout=120)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(id_ack.ack, salobj.SalRetCode.CMD_COMPLETE)
                self.assertEqual(id_ack.error, 0)
                self.assertEqual(state.summaryState, salobj.State.ENABLED)

                # Simulation loop should still be running
                self.assertTrue(harness.csc.simulated_telemetry_loop_running)
                sim_files = len(list(os.listdir(harness.csc.telemetry_directory)))
                self.assertGreaterEqual(sim_files, 2)

                await asyncio.sleep(1)

                # Move to DISABLED state
                id_ack = await harness.remote.cmd_disable.start(timeout=120)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(id_ack.ack, salobj.SalRetCode.CMD_COMPLETE)
                self.assertEqual(id_ack.error, 0)
                self.assertEqual(state.summaryState, salobj.State.DISABLED)

                # Simulation loop should still be running
                self.assertTrue(harness.csc.simulated_telemetry_loop_running)
                sim_files = len(list(os.listdir(harness.csc.telemetry_directory)))
                self.assertGreater(sim_files, 2)

                # Move to STANBY state
                id_ack = await harness.remote.cmd_standby.start(timeout=120)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(id_ack.ack, salobj.SalRetCode.CMD_COMPLETE)
                self.assertEqual(id_ack.error, 0)
                self.assertEqual(state.summaryState, salobj.State.STANDBY)

                # Simulation loop should no longer be running
                self.assertFalse(harness.csc.simulated_telemetry_loop_running)
                self.assertFalse(os.path.exists(harness.csc.telemetry_directory))

        asyncio.get_event_loop().run_until_complete(doit())


if __name__ == '__main__':
    unittest.main()
