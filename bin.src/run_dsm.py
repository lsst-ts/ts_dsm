#!/usr/bin/env python

import asyncio
import argparse

from lsst.ts import salobj
from lsst.ts.dsm import dsm_csc


def main():
    parser = argparse.ArgumentParser(f"Run DSM")
    parser.add_argument("-i", "--index", type=int, default=1,
                        help="SAL index; use the default value unless you sure you know what you are doing")
    parser.add_argument("-s", "--simulate", action="store_true",
                        help="Run in simuation mode?")
    args = parser.parse_args()
    return dsm_csc.DSMCSC(index=args.index, initial_state=salobj.State.ENABLED,
                          initial_simulation_mode=int(args.simulate))


csc = main()
asyncio.get_event_loop().run_until_complete(csc.done_task)
