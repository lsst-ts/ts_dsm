#!/usr/bin/env python

import argparse
import asyncio

from lsst.ts import salobj


async def startup(opts):
    if opts.simulate:
        settings_to_apply = opts.sim_mode + "_simulation"
    else:
        settings_to_apply = "default"

    domain = salobj.Domain()
    try:
        remote = salobj.Remote(domain=domain, name="DSM", index=opts.index)
        mode = 0
        if opts.simulate:
            mode = 1

        if opts.simulate or opts.default:
            remote.cmd_setSimulationMode.set(mode=mode)
            ack = await remote.cmd_setSimulationMode.start(timeout=120)
            if ack.ack != salobj.SalRetCode.CMD_COMPLETE:
                message = f"DSM{opts.index} failed to set simulation mode {mode} with code {ack.error}."
                raise RuntimeError(message)
        await salobj.set_summary_state(remote, salobj.State.ENABLED, settingsToApply=settings_to_apply)
    finally:
        await domain.close()


def main(opts):

    asyncio.get_event_loop().run_until_complete(startup(opts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(f"Startup a running DSM")
    parser.add_argument("-i", "--index", type=int, default=1,
                        help="SAL index; use the default value unless you sure you know what you are doing")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--simulate", action="store_true",
                       help="Run in simulation mode?")
    group.add_argument("-d", "--default", action="store_true",
                       help="Run in default (normal) mode?")
    parser.add_argument("-m", "--sim-mode", dest="sim_mode", type=str, choices=["fast", "slow"],
                        default="fast",
                        help="Set speed of simulation loop via configuration.")
    args = parser.parse_args()

    main(args)
