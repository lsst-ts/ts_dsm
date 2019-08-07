#!/usr/bin/env python

import argparse
import asyncio

from lsst.ts import salobj


async def startup(opts):
    if opts.simulate:
        settings_to_apply = "simulation"
    else:
        settings_to_apply = "default"

    domain = salobj.Domain()
    try:
        remote = salobj.Remote(domain=domain, name="DSM", index=opts.index)
        if opts.simulate:
            remote.cmd_setSimulationMode.set(mode=1)
            ack = await remote.cmd_setSimulationMode.start(timeout=120)
            if ack.ack != salobj.SalRetCode.CMD_COMPLETE:
                raise RuntimeError(f"DSM{opts.index} failed to set simulation mode with code {ack.error}.")
        await salobj.set_summary_state(remote, salobj.State.ENABLED, settingsToApply=settings_to_apply)
    finally:
        await domain.close()


def main(opts):

    asyncio.get_event_loop().run_until_complete(startup(opts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(f"Startup a running DSM")
    parser.add_argument("-i", "--index", type=int, default=1,
                        help="SAL index; use the default value unless you sure you know what you are doing")
    parser.add_argument("-s", "--simulate", action="store_true",
                        help="Run in simuation mode?")
    args = parser.parse_args()

    main(args)
