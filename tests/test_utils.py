import unittest

from lsst.ts.dsm import utils


class TestUtils(unittest.TestCase):
    def test_convert_time(self):
        time_string = "2019-08-08T22:26:52.451723"
        tai_time_stamp = 1565303249.451723
        self.assertEqual(utils.convert_time(time_string), tai_time_stamp)

        time_string = "2016-12-31T23:59:59.951723"
        tai_time_stamp = 1483228835.951723
        self.assertEqual(utils.convert_time(time_string), tai_time_stamp)

        time_string = "2016-12-31T23:59:60.351723"
        tai_time_stamp = 1483228836.351723
        self.assertEqual(utils.convert_time(time_string), tai_time_stamp)

        time_string = "2017-01-01T00:00:00.151723"
        tai_time_stamp = 1483228837.151723
        self.assertEqual(utils.convert_time(time_string), tai_time_stamp)


if __name__ == "__main__":
    unittest.main()
