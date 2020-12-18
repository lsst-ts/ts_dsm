#!/usr/bin/env python

import asyncio

from lsst.ts.dsm import dsm_csc


if __name__ == "__main__":
    asyncio.run(dsm_csc.DSMCSC.amain(index=True))
