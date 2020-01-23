#!/usr/bin/env python

import asyncio
import argparse

from lsst.ts import salobj
from lsst.ts.dsm import dsm_csc


async def go_to_enabled(csc_domain, options):
    remote = salobj.Remote(domain=csc_domain, name="DSM", index=options.index)
    await remote.evt_heartbeat.next(flush=False, timeout=120)

    commands = ['start', 'enable']
    for command in commands:
        cmd = getattr(remote, f'cmd_{command}')
        if command == 'start':
            cmd.set(settingsToApply="default")
        await cmd.start(timeout=15)

async def main(opts):

    csc = dsm_csc.DSMCSC(index=opts.index, simulation_mode=opts.mode)

    await asyncio.gather(csc.done_task, go_to_enabled(csc.domain, opts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Startup the DSM CSC. Default mode is real time telemetry.")
    parser.add_argument("-i", "--index", type=int, default=1,
                        help="SAL index; use the default value unless you sure you know what you are doing")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-f", "--fast", dest="mode", action="store_const", const=1,
                       help="Run CSC in fast (1 sec) telemetry simulation mode")
    group.add_argument("-s", "--slow", dest="mode", action="store_const", const=2,
                       help="Run CSC in slow (30 sec) telemetry simulation mode")
    parser.set_defaults(mode=0)
    args = parser.parse_args()

    asyncio.run(main(args))
