import unittest
import pathlib

from lsst.ts import salobj


class BlackTestCase(unittest.TestCase):
    def test_black_formatted(self):
        salobj.assert_black_formatted(pathlib.Path(__file__).parents[1])


if __name__ == "__main__":
    unittest.main()
