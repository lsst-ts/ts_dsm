#!/usr/bin/env python

import argparse
import asyncio

from lsst.ts import salobj


async def shutdown(opts):
    if opts.full:
        final_state = salobj.State.OFFLINE
    else:
        final_state = salobj.State.STANDBY

    domain = salobj.Domain()
    try:
        remote = salobj.Remote(domain=domain, name="DSM", index=opts.index)
        await salobj.set_summary_state(remote, final_state)
    finally:
        await domain.close()


def main(opts):

    asyncio.run(shutdown(opts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Shutdown (default: STANDBY) the DSM CSC.")
    parser.add_argument("-i", "--index", type=int, default=1,
                        help="SAL index; use the default value unless you sure you know what you are doing")
    parser.add_argument("-f", "--full", action="store_true",
                        help="Take CSC to OFFLINE state.")
    args = parser.parse_args()

    main(args)
