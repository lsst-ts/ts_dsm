import csv
from datetime import datetime, timedelta
import os
import yaml

import numpy as np

__all__ = ['create_telemetry_config', 'create_telemetry_data']


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

    content = {'ui_versions': {'code': ui_version, 'config': ui_config_version,
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
    now = datetime.utcnow()
    first = now - timedelta(seconds=25)
    rms_roi = np.random.random()

    output = [now.isoformat(), first.isoformat(), now.isoformat(), rms_roi, rms_roi]

    telemetry_file = 'dsm_{}.dat'.format(now.strftime('%Y%m%d_%H%M%S'))
    with open(os.path.join(output_dir, telemetry_file), 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(output)
