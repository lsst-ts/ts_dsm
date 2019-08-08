import unittest

from lsst.ts.dsm import utils


class TestUtils(unittest.TestCase):

    def test_convert_time(self):
        time_string = '2019-08-08T22:26:52.451723'
        tai_time_stamp = 1565303249.451723

        self.assertEqual(utils.convert_time(time_string), tai_time_stamp)


if __name__ == '__main__':
    unittest.main()
