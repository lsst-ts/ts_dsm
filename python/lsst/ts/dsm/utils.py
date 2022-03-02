import csv
import os
import yaml

from astropy.time import Time, TimeDelta
import numpy as np

from lsst.ts import utils

__all__ = ["convert_time", "create_telemetry_config", "create_telemetry_data"]


def convert_time(in_time):
    """Convert an ISO UTC timestring to TAI timestamp.

    Parameters
    ----------
    in_time : `str`
        The time to convert.

    Returns
    -------
    float
        The TAI time corresponding to the input.
    """
    ptime = Time(in_time, scale="utc")
    return utils.tai_from_utc(ptime)


def create_telemetry_config(output_dir, sim_loop_time):
    """Create the DSM UI Configuration file for simulation mode.

    Parameters
    ----------
    output_dir : `str`
        Directory to write the telemetry UI configuration file.
    sim_loop_time : `int` or `float`
        The time in seconds between successive telemetry file generations.
    """
    ui_version = "1.0.1"
    ui_config_version = "1.4.4"
    ui_config_file = "/dsm/ui_dsm_config/default.yaml"
    camera_name = "Sim_Camera"
    if sim_loop_time > 1:
        camera_fps = 40
        data_buffer_size = 1024
    else:
        camera_fps = 120
        data_buffer_size = 128
    data_acquisition_time = sim_loop_time

    content = dict(
        timestamp=Time.now().isot,
        ui_versions=dict(
            code=ui_version,
            config=ui_config_version,
            config_file=ui_config_file,
        ),
        camera=dict(name=camera_name, fps=camera_fps),
        data=dict(
            buffer_size=data_buffer_size,
            acquisition_time=data_acquisition_time,
        ),
    )

    filename = os.path.join(output_dir, "dsm_ui_config.yaml")
    with open(filename, "w") as ofile:
        yaml.dump(content, ofile)


def create_telemetry_data(output_dir, sim_loop_time):
    """Create the DSM UI telemetry file for simulation mode.

    Parameters
    ----------
    output_dir : `str`
        Directory to write the telemetry data file.
    """
    now = Time.now()
    first = now - TimeDelta(sim_loop_time, format="sec")
    rms_roi = np.random.random()
    centroidX = 214 + 3 * np.random.random()
    centroidY = 320 + 3 * np.random.random()
    flux = 2000 + 100 * np.random.random()
    maxADC = 1000 + 100 * np.random.random()
    fwhm = 6 + np.random.random()

    output = [
        now.isot,
        first.isot,
        now.isot,
        rms_roi,
        rms_roi,
        centroidX,
        centroidY,
        flux,
        maxADC,
        fwhm,
    ]

    telemetry_file = "dsm_{}.dat".format(now.strftime("%Y%m%d_%H%M%S"))
    with open(os.path.join(output_dir, telemetry_file), "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(output)
