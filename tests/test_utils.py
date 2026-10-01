# This file is part of ts_dsm.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import unittest

from lsst.ts.dsm import utils


class TestUtils(unittest.TestCase):
    def test_convert_time(self):
        places = 6

        time_string = "2019-08-08T22:26:52.451723"
        tai_time_stamp = 1565303249.451723
        self.assertAlmostEqual(
            utils.convert_time(time_string), tai_time_stamp, places=places
        )

        time_string = "2016-12-31T23:59:59.951723"
        tai_time_stamp = 1483228835.951723
        self.assertAlmostEqual(
            utils.convert_time(time_string), tai_time_stamp, places=places
        )

        time_string = "2016-12-31T23:59:60.351723"
        tai_time_stamp = 1483228836.351723
        self.assertAlmostEqual(
            utils.convert_time(time_string), tai_time_stamp, places=places
        )

        time_string = "2017-01-01T00:00:00.151723"
        tai_time_stamp = 1483228837.151723
        self.assertAlmostEqual(
            utils.convert_time(time_string), tai_time_stamp, places=places
        )


if __name__ == "__main__":
    unittest.main()
