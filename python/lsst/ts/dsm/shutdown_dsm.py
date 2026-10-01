# This file is part of ts_dsm.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

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
