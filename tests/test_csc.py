import unittest
import asyncio
import numpy as np
import os
import pathlib
import shutil
import yaml

from lsst.ts import salobj

from lsst.ts.dsm import dsm_csc

np.random.seed(47)

index_gen = salobj.index_generator()

STD_TIMEOUT = 5
LONG_TIMEOUT = 20  # timeout for starting SAL components (sec)
TEST_CONFIG_DIR = pathlib.Path(__file__).parents[1].joinpath("tests", "data", "config")


class Harness:
    def __init__(self, initial_state, config_dir=None):
        salobj.test_utils.set_random_lsst_dds_domain()
        self.index = 1
        self.csc = dsm_csc.DSMCSC(index=self.index, config_dir=config_dir,
                                  initial_state=initial_state,
                                  initial_simulation_mode=1)
        self.remote = salobj.Remote(domain=self.csc.domain, name="DSM", index=self.index)

    async def __aenter__(self):
        await self.csc.start_task
        await self.remote.start_task
        return self

    async def __aexit__(self, *args):
        await self.csc.close()


class TestDSMCSC(unittest.TestCase):

    def setUp(self):
        self.telemetry_directory = ""

    def tearDown(self):
        self.cleanup(self.telemetry_directory)

    def cleanup(self, directory):
        """Cleanup telemetry directory if tests fail.
        """
        if os.path.exists(directory):
            shutil.rmtree(directory)

    def test_lifecycle_behavior(self):
        """Test that the DSM through the standard lifecycle.

        The emphasis for this test is making sure the telemetry loop can be
        started and stopped through the lifecycle commands.
        """
        async def doit():
            async with Harness(initial_state=salobj.State.STANDBY, config_dir=TEST_CONFIG_DIR) as harness:
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.STANDBY)
                self.assertEqual(harness.csc.simulation_mode, 1)
                self.assertIsNone(harness.csc.telemetry_directory)
                self.assertIsNone(harness.csc.config)

                # Move to DISABLED state
                harness.remote.cmd_start.set(settingsToApply='fast_simulation')
                await harness.remote.cmd_start.start(timeout=LONG_TIMEOUT)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.DISABLED)
                self.telemetry_directory = harness.csc.telemetry_directory

                # Check that the simulated telemetry loop is running
                self.assertIsNotNone(harness.csc.telemetry_directory)
                self.assertTrue(os.path.exists(harness.csc.telemetry_directory))
                self.telemetry_directory = harness.csc.telemetry_directory
                self.assertTrue(harness.csc.simulated_telemetry_loop_running)
                sim_files = len(list(os.listdir(harness.csc.telemetry_directory)))
                self.assertEqual(sim_files, 2)

                # Check that the telemetry loop is running
                self.assertTrue(harness.csc.telemetry_loop_running)
                configuration = await harness.remote.tel_configuration.next(flush=True, timeout=LONG_TIMEOUT)
                self.assertEqual(configuration.dsmIndex, 1)
                self.assertGreater(configuration.timestampConfigStart, 0)
                self.assertEqual(configuration.uiVersionCode, '1.0.1')
                self.assertEqual(configuration.uiVersionConfig, '1.4.4')
                self.assertEqual(configuration.uiConfigFile, 'file:///dsm/ui_dsm_config/default.yaml')
                self.assertEqual(configuration.cameraName, 'Vimba')
                self.assertEqual(configuration.cameraFps, 40)
                self.assertEqual(configuration.dataBufferSize, 1024)
                self.assertEqual(configuration.dataAcquisitionTime, 25)

                dome_seeing = await harness.remote.tel_domeSeeing.next(flush=True, timeout=STD_TIMEOUT)
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

                # Move to ENABLED state
                await harness.remote.cmd_enable.start(timeout=LONG_TIMEOUT)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.ENABLED)

                # Simulation loop should still be running
                self.assertTrue(harness.csc.simulated_telemetry_loop_running)
                sim_files = len(list(os.listdir(harness.csc.telemetry_directory)))
                self.assertGreaterEqual(sim_files, 2)

                # Telemetry loop should still be running
                self.assertTrue(harness.csc.telemetry_loop_running)

                await asyncio.sleep(1)

                # Move to DISABLED state
                await harness.remote.cmd_disable.start(timeout=LONG_TIMEOUT)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.DISABLED)

                # Simulation loop should still be running
                self.assertTrue(harness.csc.simulated_telemetry_loop_running)
                sim_files = len(list(os.listdir(harness.csc.telemetry_directory)))
                self.assertGreater(sim_files, 2)

                # Telemetry loop should still be running
                self.assertTrue(harness.csc.telemetry_loop_running)

                # Move to STANDBY state
                await harness.remote.cmd_standby.start(timeout=LONG_TIMEOUT)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.STANDBY)

                # Simulation loop should no longer be running
                self.assertFalse(harness.csc.simulated_telemetry_loop_running)
                self.assertFalse(harness.csc.simulated_telemetry_ui_config_written)

                # Telemetry loop should no longer be running
                self.assertFalse(harness.csc.telemetry_loop_running)

        asyncio.get_event_loop().run_until_complete(doit())

    def test_default_config_dir(self):
        async def doit():
            async with Harness(initial_state=salobj.State.STANDBY) as harness:
                self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)

                desired_config_pkg_name = "ts_config_eas"
                desired_config_env_name = desired_config_pkg_name.upper() + "_DIR"
                desird_config_pkg_dir = os.environ[desired_config_env_name]
                desired_config_dir = pathlib.Path(desird_config_pkg_dir) / "DSM/v1"
                self.assertEqual(harness.csc.get_config_pkg(), desired_config_pkg_name)
                self.assertEqual(harness.csc.config_dir, desired_config_dir)

        asyncio.get_event_loop().run_until_complete(doit())

    def test_configuration(self):
        async def doit():
            async with Harness(initial_state=salobj.State.STANDBY, config_dir=TEST_CONFIG_DIR) as harness:
                self.assertEqual(harness.csc.summary_state, salobj.State.STANDBY)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.STANDBY)
                settings = await harness.remote.evt_settingVersions.next(flush=False, timeout=LONG_TIMEOUT)
                settings_labels = ("fast_simulation", "slow_simulation")
                for label in settings.recommendedSettingsLabels.split(','):
                    self.assertTrue(label in settings_labels)
                self.assertEqual(settings.settingsUrl, TEST_CONFIG_DIR.as_uri())

                harness.remote.cmd_start.set(settingsToApply="fast_simulation")
                await harness.remote.cmd_start.start(timeout=STD_TIMEOUT)
                self.assertEqual(harness.csc.summary_state, salobj.State.DISABLED)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=STD_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.DISABLED)
                settings_applied = await harness.remote.evt_settingsApplied.next(flush=False,
                                                                                 timeout=STD_TIMEOUT)
                self.assertTrue(settings_applied.telemetryDirectory.startswith('/tmp'))
                self.assertEqual(settings_applied.simulationLoopTime, 1)
                config_path = os.path.join(TEST_CONFIG_DIR, "fast_simulation.yaml")
                with open(config_path, "r") as f:
                    config_raw = f.read()
                config_data = yaml.safe_load(config_raw)
                for field, value in config_data.items():
                    self.assertEqual(getattr(harness.csc.config, field), value)
                self.assertTrue(harness.csc.telemetry_directory.startswith('/tmp'))
                self.assertEqual(harness.csc.simulation_loop_time, harness.csc.config.simulation_loop_time)
                self.assertGreater(harness.csc.config.simulation_loop_time, 0)
                self.telemetry_directory = harness.csc.telemetry_directory

                # Return to STANDBY to shutdown loops
                await harness.remote.cmd_standby.start(timeout=LONG_TIMEOUT)
                state = await harness.remote.evt_summaryState.next(flush=False, timeout=LONG_TIMEOUT)
                self.assertEqual(state.summaryState, salobj.State.STANDBY)

        asyncio.get_event_loop().run_until_complete(doit())


if __name__ == '__main__':
    unittest.main()
