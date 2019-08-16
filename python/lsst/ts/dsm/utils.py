import csv
import os
import yaml

from astropy.time import Time, TimeDelta
import numpy as np
import pytz

__all__ = ['convert_time', 'create_telemetry_config', 'create_telemetry_data']


def convert_time(in_time):
    """Convert an ISO UTC timestring to TAI timestamp.

    Parameters
    ----------
    in_time : str
        The time to convert.

    Returns
    -------
    float
        The TAI time corresponding to the input.
    """
    ptime = Time(in_time, scale='utc')
    # replace allows this to work if clock isn't in UTC.
    return ptime.tai.datetime.replace(tzinfo=pytz.utc).timestamp()


def create_telemetry_config(output_dir):
    """Create the DSM UI Configuration file for simulation mode.

    Parameters
    ----------
    output_dir : str
        Directory to write the telemetry UI configuration file.
    """
    ui_version = '1.0.1'
    ui_config_version = '1.4.4'
    ui_config_file = '/dsm/ui_dsm_config/default.yaml'
    camera_name = 'Vimba'
    camera_fps = 40
    data_buffer_size = 1024
    data_acquisition_time = 25

    content = {'timestamp': Time.now().isot,
               'ui_versions': {'code': ui_version, 'config': ui_config_version,
                               'config_file': ui_config_file},
               'camera': {'name': camera_name,
                          'fps': camera_fps},
               'data': {'buffer_size': data_buffer_size,
                        'acquisition_time': data_acquisition_time}}

    filename = os.path.join(output_dir, 'dsm_ui_config.yaml')
    with open(filename, 'w') as ofile:
        yaml.dump(content, ofile)


def create_telemetry_data(output_dir):
    """
    Parameters
    ----------
    output_dir : str
        Directory to write the telemetry data file.
    """
    now = Time.now()
    first = now - TimeDelta(25, format='sec')
    rms_roi = np.random.random()

    output = [now.isot, first.isot, now.isot, rms_roi, rms_roi]

    telemetry_file = 'dsm_{}.dat'.format(now.strftime('%Y%m%d_%H%M%S'))
    with open(os.path.join(output_dir, telemetry_file), 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(output)
