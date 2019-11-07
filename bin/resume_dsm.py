#!/usr/bin/env python

import argparse
import asyncio

from lsst.ts import salobj


async def startup(opts):
    domain = salobj.Domain()
    try:
        remote = salobj.Remote(domain=domain, name="DSM", index=opts.index)
        remote.cmd_setSimulationMode.set(mode=opts.mode)
        ack = await remote.cmd_setSimulationMode.start(timeout=120)
        if ack.ack != salobj.SalRetCode.CMD_COMPLETE:
            message = f"DSM{opts.index} failed to set simulation mode {opts.mode} with code {ack.error}."
            raise RuntimeError(message)
        await salobj.set_summary_state(remote, salobj.State.ENABLED, settingsToApply="default")
    finally:
        await domain.close()


def main(opts):

    asyncio.run(startup(opts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Resume the DSM CSC.")
    parser.add_argument("-i", "--index", type=int, default=1,
                        help="SAL index; use the default value unless you sure you know what you are doing")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--fast", dest="mode", action="store_const", const=1,
                       help="Run CSC in fast (1 sec) telemetry simulation mode")
    group.add_argument("-s", "--slow", dest="mode", action="store_const", const=2,
                       help="Run CSC in slow (30 sec) telemetry simulation mode")
    parser.set_defaults(mode=0)
    args = parser.parse_args()

    main(args)
