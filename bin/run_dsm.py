#!/usr/bin/env python

import asyncio
import argparse

from lsst.ts import salobj
from lsst.ts.dsm import dsm_csc


async def go_to_enabled(csc_domain, options):
    remote = salobj.Remote(domain=csc_domain, name="DSM", index=options.index)
    await remote.start_task
    await remote.evt_heartbeat.next(flush=False, timeout=120)
    await salobj.set_summary_state(remote, salobj.State.ENABLED)


async def main(opts):

    csc = dsm_csc.DSMCSC(index=opts.index, simulation_mode=opts.simulate)

    await asyncio.gather(csc.done_task, go_to_enabled(csc.domain, opts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Startup the DSM CSC. Default mode is real time telemetry."
    )
    parser.add_argument(
        "-i",
        "--index",
        type=int,
        default=1,
        help="SAL index; use the default value unless you sure you know what you are doing",
    )
    parser.add_argument(
        "--simulate",
        dest="simulate",
        choices=[0, 1, 2],
        type=int,
        default=0,
        help="Set the operation mode: 0 (real), 1 (fast sim, 1 sec), 2 (slow sim, 30 sec)",
    )
    args = parser.parse_args()

    asyncio.run(main(args))
