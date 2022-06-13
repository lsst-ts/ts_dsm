import argparse
import asyncio

from lsst.ts import salobj

__all__ = ["shutdown_dsm"]


async def shutdown(opts):
    end_state = getattr(salobj.State, opts.state.upper())

    domain = salobj.Domain()
    try:
        remote = salobj.Remote(domain=domain, name="DSM", index=opts.index)
        await remote.start_task
        await salobj.set_summary_state(remote, end_state)
    finally:
        await domain.close()


def shutdown_dsm():
    parser = argparse.ArgumentParser(description="Shutdown the DSM CSC.")
    parser.add_argument(
        "index",
        type=int,
        help="SAL index; Must match the index to the running process you wish to terminate.",
    )
    parser.add_argument(
        "--state", choices=["standby", "offline"], help="Set the shutdown state."
    )
    args = parser.parse_args()

    asyncio.run(shutdown(args))
