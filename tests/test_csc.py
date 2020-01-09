import unittest
import asyncio
import numpy as np
import os
import pathlib
import shutil

import asynctest

from lsst.ts import salobj
from lsst.ts.dsm import dsm_csc

np.random.seed(47)

index_gen = salobj.index_generator()

STD_TIMEOUT = 5
LONG_TIMEOUT = 20  # timeout for starting SAL components (sec)
TEST_CONFIG_DIR = pathlib.Path(__file__).parents[1].joinpath("tests", "data", "config")


class TestDSMCSC(asynctest.TestCase):

    def setUp(self):
        salobj.test_utils.set_random_lsst_dds_domain()
        self.telemetry_directory = ""
        self.csc = None
        self.remote = None

    async def tearDown(self):
        self.cleanup(self.telemetry_directory)
        if self.remote is not None:
            await self.remote.close()
        if self.csc is not None:
            await self.csc.close()

    def cleanup(self, directory):
        """Cleanup telemetry directory if tests fail.
        """
        if os.path.exists(directory):
            shutil.rmtree(directory)

    async def make_csc(self, initial_state, config_dir=None):
        """Make a DSM CSC and remote and wait for them to start.
        """
        self.index = 1
        self.csc = dsm_csc.DSMCSC(index=self.index, config_dir=config_dir,
                                  initial_state=initial_state,
                                  initial_simulation_mode=1)
        self.remote = salobj.Remote(domain=self.csc.domain, name="DSM", index=self.index)

        await self.csc.start_task
        await self.remote.start_task

    async def test_lifecycle_behavior(self):
        """Test that the DSM through the standard lifecycle.

        The emphasis for this test is making sure the telemetry loop can be
        started and stopped through the lifecycle commands.
        """
        await self.make_csc(initial_state=salobj.State.STANDBY, config_dir=TEST_CONFIG_DIR)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.STANDBY)
        self.assertEqual(self.csc.simulation_mode, 1)
        self.assertIsNotNone(self.csc.telemetry_directory)
        # self.assertIsNone(self.csc.telemetry_directory)
        self.telemetry_directory = self.csc.telemetry_directory
        self.assertIsNone(self.csc.config)

        # Move to DISABLED state
        self.remote.cmd_start.set(settingsToApply='default')
        await self.remote.cmd_start.start(timeout=LONG_TIMEOUT)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.DISABLED)
        self.telemetry_directory = self.csc.telemetry_directory

        # Check that the simulated telemetry loop is running
        self.assertIsNotNone(self.csc.telemetry_directory)
        self.assertTrue(os.path.exists(self.csc.telemetry_directory))
        self.telemetry_directory = self.csc.telemetry_directory
        self.assertFalse(self.csc.simulated_telemetry_loop_task.done())
        sim_files = len(list(os.listdir(self.csc.telemetry_directory)))
        self.assertEqual(sim_files, 2)

        # Check that the telemetry loop is running
        self.assertFalse(self.csc.telemetry_loop_task.done())
        configuration = await self.remote.tel_configuration.next(flush=True, timeout=LONG_TIMEOUT)
        self.assertEqual(configuration.dsmIndex, 1)
        self.assertGreater(configuration.timestampConfigStart, 0)
        self.assertEqual(configuration.uiVersionCode, '1.0.1')
        self.assertEqual(configuration.uiVersionConfig, '1.4.4')
        self.assertEqual(configuration.uiConfigFile, 'file:///dsm/ui_dsm_config/default.yaml')
        self.assertEqual(configuration.cameraName, 'Vimba')
        self.assertEqual(configuration.cameraFps, 40)
        self.assertEqual(configuration.dataBufferSize, 1024)
        self.assertEqual(configuration.dataAcquisitionTime, 25)

        dome_seeing = await self.remote.tel_domeSeeing.next(flush=True, timeout=STD_TIMEOUT)
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

        # Move to ENABLED state
        await self.remote.cmd_enable.start(timeout=LONG_TIMEOUT)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.ENABLED)

        # Simulation loop should still be running
        self.assertFalse(self.csc.simulated_telemetry_loop_task.done())
        sim_files = len(list(os.listdir(self.csc.telemetry_directory)))
        self.assertGreaterEqual(sim_files, 2)

        # Telemetry loop should still be running
        self.assertFalse(self.csc.telemetry_loop_task.done())

        await asyncio.sleep(1)

        # Move to DISABLED state
        await self.remote.cmd_disable.start(timeout=LONG_TIMEOUT)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.DISABLED)

        # Simulation loop should still be running
        self.assertFalse(self.csc.simulated_telemetry_loop_task.done())
        sim_files = len(list(os.listdir(self.csc.telemetry_directory)))
        self.assertGreater(sim_files, 2)

        # Telemetry loop should still be running
        self.assertFalse(self.csc.telemetry_loop_task.done())

        # Move to STANDBY state
        await self.remote.cmd_standby.start(timeout=LONG_TIMEOUT)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.STANDBY)

        # Simulation loop should no longer be running
        self.assertTrue(self.csc.simulated_telemetry_loop_task.done())
        self.assertFalse(self.csc.simulated_telemetry_ui_config_written)

        # Telemetry loop should no longer be running
        self.assertTrue(self.csc.telemetry_loop_task.done())

    async def test_default_config_dir(self):
        await self.make_csc(initial_state=salobj.State.STANDBY)
        self.assertEqual(self.csc.summary_state, salobj.State.STANDBY)

        desired_config_pkg_name = "ts_config_eas"
        desired_config_env_name = desired_config_pkg_name.upper() + "_DIR"
        desird_config_pkg_dir = os.environ[desired_config_env_name]
        desired_config_dir = pathlib.Path(desird_config_pkg_dir) / "DSM/v1"
        self.assertEqual(self.csc.get_config_pkg(), desired_config_pkg_name)
        self.assertEqual(self.csc.config_dir, desired_config_dir)
        self.telemetry_directory = self.csc.telemetry_directory

    async def test_configuration(self):
        await self.make_csc(initial_state=salobj.State.STANDBY, config_dir=TEST_CONFIG_DIR)
        self.assertEqual(self.csc.summary_state, salobj.State.STANDBY)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.STANDBY)
        settings = await self.remote.evt_settingVersions.next(flush=False, timeout=LONG_TIMEOUT)
        settings_labels = ("default", "alternate")
        for label in settings.recommendedSettingsLabels.split(','):
            self.assertTrue(label in settings_labels)
        self.assertEqual(settings.settingsUrl, TEST_CONFIG_DIR.as_uri())

        self.remote.cmd_start.set(settingsToApply="default")
        await self.remote.cmd_start.start(timeout=STD_TIMEOUT)
        self.assertEqual(self.csc.summary_state, salobj.State.DISABLED)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.DISABLED)
        settings_applied = await self.remote.evt_settingsAppliedSetup.next(flush=False,
                                                                           timeout=STD_TIMEOUT)
        self.assertTrue(settings_applied.telemetryDirectory.startswith('/tmp'))
        self.assertEqual(settings_applied.simulationLoopTime, 1)
        self.assertTrue(self.csc.telemetry_directory.startswith('/tmp'))
        self.assertEqual(self.csc.simulation_loop_time, 1)
        self.telemetry_directory = self.csc.telemetry_directory

        # Return to STANDBY to shutdown loops
        await self.remote.cmd_standby.start(timeout=LONG_TIMEOUT)
        state = await self.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
        self.assertEqual(state.summaryState, salobj.State.STANDBY)


if __name__ == '__main__':
    unittest.main()
