#!/usr/bin/env python

import asyncio
import argparse

from lsst.ts import salobj
from lsst.ts.dsm import dsm_csc


async def go_to_enabled(csc_domain, csc_index, is_simulation):
    remote = salobj.Remote(domain=csc_domain, name="DSM", index=csc_index)
    await remote.evt_heartbeat.next(flush=False, timeout=120)

    if is_simulation:
        settings_to_apply = "simulation"
    else:
        settings_to_apply = "default"

    await salobj.set_summary_state(remote, salobj.State.ENABLED, settingsToApply=settings_to_apply)


def main(opts):

    csc = dsm_csc.DSMCSC(index=opts.index, initial_simulation_mode=int(opts.simulate))

    asyncio.get_event_loop().run_until_complete(asyncio.gather(csc.done_task,
                                                               go_to_enabled(csc.domain,
                                                                             opts.index,
                                                                             opts.simulate)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(f"Run DSM")
    parser.add_argument("-i", "--index", type=int, default=1,
                        help="SAL index; use the default value unless you sure you know what you are doing")
    parser.add_argument("-s", "--simulate", action="store_true",
                        help="Run in simuation mode?")
    args = parser.parse_args()

    main(args)
