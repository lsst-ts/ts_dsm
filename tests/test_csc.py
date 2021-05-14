import asyncio
import os
import shutil
import unittest

import numpy as np

from lsst.ts import salobj
from lsst.ts.dsm import dsm_csc

np.random.seed(47)

index_gen = salobj.index_generator()

STD_TIMEOUT = 5
LONG_TIMEOUT = 20  # timeout for starting SAL components (sec)


class TestDSMCSC(salobj.BaseCscTestCase, unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        salobj.set_random_lsst_dds_partition_prefix()
        self.telemetry_directory = ""

    def tearDown(self):
        self.cleanup(self.telemetry_directory)

    def cleanup(self, directory):
        """Cleanup telemetry directory if tests fail."""
        if os.path.exists(directory):
            shutil.rmtree(directory)

    def basic_make_csc(self, initial_state, config_dir, simulation_mode):
        """Make a DSM CSC."""
        return dsm_csc.DSMCSC(
            index=1,
            initial_state=initial_state,
            simulation_mode=simulation_mode,
        )

    async def test_lifecycle_behavior(self):
        """Test that the DSM through the standard lifecycle.

        The emphasis for this test is making sure the telemetry loop can be
        started and stopped through the lifecycle commands.
        """
        async with self.make_csc(initial_state=salobj.State.STANDBY, simulation_mode=1):
            state = await self.remote.evt_summaryState.next(
                flush=False, timeout=LONG_TIMEOUT
            )
            self.assertEqual(state.summaryState, salobj.State.STANDBY)
            self.assertEqual(self.csc.simulation_mode, 1)
            self.assertIsNotNone(self.csc.telemetry_directory)
            # self.assertIsNone(self.csc.telemetry_directory)
            self.telemetry_directory = self.csc.telemetry_directory

            # Move to DISABLED state
            await self.remote.cmd_start.start(timeout=LONG_TIMEOUT)
            state = await self.remote.evt_summaryState.next(
                flush=False, timeout=LONG_TIMEOUT
            )
            self.assertEqual(state.summaryState, salobj.State.DISABLED)
            self.telemetry_directory = self.csc.telemetry_directory

            # Check that the telemetry loops aren't running yet.
            self.assertTrue(self.csc.simulated_telemetry_loop_task.done())
            self.assertTrue(self.csc.telemetry_loop_task.done())

            # Move to ENABLED state
            await self.remote.cmd_enable.start(timeout=LONG_TIMEOUT)
            state = await self.remote.evt_summaryState.next(
                flush=False, timeout=LONG_TIMEOUT
            )
            self.assertEqual(state.summaryState, salobj.State.ENABLED)

            # Check that the simulated telemetry loop is running
            self.assertIsNotNone(self.csc.telemetry_directory)
            self.assertTrue(os.path.exists(self.csc.telemetry_directory))
            self.telemetry_directory = self.csc.telemetry_directory
            self.assertFalse(self.csc.simulated_telemetry_loop_task.done())
            sim_files = len(list(os.listdir(self.csc.telemetry_directory)))
            self.assertEqual(sim_files, 1)

            # Check that the telemetry loop is running
            self.assertFalse(self.csc.telemetry_loop_task.done())
            try:
                config_msg = self.remote.evt_configuration
            except AttributeError:
                config_msg = self.remote.tel_configuration
            configuration = await config_msg.next(flush=False, timeout=LONG_TIMEOUT)
            self.assertEqual(configuration.dsmIndex, 1)
            self.assertGreater(configuration.timestampConfigStart, 0)
            self.assertEqual(configuration.uiVersionCode, "1.0.1")
            self.assertEqual(configuration.uiVersionConfig, "1.4.4")
            self.assertEqual(
                configuration.uiConfigFile, "file:///dsm/ui_dsm_config/default.yaml"
            )
            self.assertEqual(configuration.cameraName, "Sim_Camera")
            self.assertEqual(configuration.cameraFps, 120)
            self.assertEqual(configuration.dataBufferSize, 128)
            self.assertEqual(configuration.dataAcquisitionTime, 1)

            dome_seeing = await self.remote.tel_domeSeeing.next(
                flush=False, timeout=STD_TIMEOUT
            )
            self.assertEqual(dome_seeing.dsmIndex, 1)
            self.assertIsInstance(dome_seeing.timestampCurrent, float)
            self.assertIsInstance(dome_seeing.timestampFirstMeasurement, float)
            self.assertIsInstance(dome_seeing.timestampLastMeasurement, float)
            self.assertIsInstance(dome_seeing.rmsX, float)
            self.assertGreater(dome_seeing.rmsX, 0)
            self.assertIsInstance(dome_seeing.rmsY, float)
            self.assertGreater(dome_seeing.rmsY, 0)
            # Only for simulation!
            self.assertEqual(dome_seeing.rmsX, dome_seeing.rmsY)
            self.assertIsInstance(dome_seeing.centroidX, float)
            self.assertGreaterEqual(dome_seeing.centroidX, 215)
            self.assertIsInstance(dome_seeing.centroidY, float)
            self.assertGreaterEqual(dome_seeing.centroidY, 320)
            self.assertIsInstance(dome_seeing.flux, float)
            self.assertGreaterEqual(dome_seeing.flux, 2000)
            self.assertIsInstance(dome_seeing.maxADC, float)
            self.assertGreaterEqual(dome_seeing.maxADC, 1000)
            self.assertIsInstance(dome_seeing.fwhm, float)
            self.assertGreaterEqual(dome_seeing.fwhm, 6)

            await asyncio.sleep(1)

            # Move to DISABLED state
            await self.remote.cmd_disable.start(timeout=LONG_TIMEOUT)
            state = await self.remote.evt_summaryState.next(
                flush=False, timeout=LONG_TIMEOUT
            )
            self.assertEqual(state.summaryState, salobj.State.DISABLED)

            # Telemetry loops should stop running
            self.assertTrue(self.csc.simulated_telemetry_loop_task.done())
            self.assertTrue(self.csc.telemetry_loop_task.done())
            self.assertFalse(self.csc.simulated_telemetry_ui_config_written)

            # Move to STANDBY state
            await self.remote.cmd_standby.start(timeout=LONG_TIMEOUT)
            state = await self.remote.evt_summaryState.next(
                flush=False, timeout=LONG_TIMEOUT
            )
            self.assertEqual(state.summaryState, salobj.State.STANDBY)

    def test_bad_simulation_mode(self):
        """Test to ensure bad simulation modes raise"""
        with self.assertRaises(ValueError):
            dsm_csc.DSMCSC(
                index=1,
                initial_state=salobj.State.STANDBY,
                simulation_mode=3,
            )


if __name__ == "__main__":
    unittest.main()
