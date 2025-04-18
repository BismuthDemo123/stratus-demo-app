#!/usr/bin/env python3
from datetime import datetime, timedelta
from typing import Optional

import argparse
import logging

from wx_explore.common.log_setup import init_sentry
from wx_explore.common.utils import datetime2unix
from wx_explore.ingest.common import get_queue
from wx_explore.ingest.sources.source import IngestSource


class NAM(IngestSource):
    SOURCE_NAME = "nam"

    @staticmethod
    def queue(
            time_min: int = 0,
            time_max: int = 60,
            run_time: Optional[datetime] = None,
            acquire_time: Optional[datetime] = None
    ):
        if run_time is None:
            # nam is run every 6 hours
            run_time = datetime.utcnow()
            run_time = run_time.replace(hour=(run_time.hour//6)*6, minute=0, second=0, microsecond=0)

        if acquire_time is None:
            # the first files are available 1hr 45min after
            acquire_time = run_time
            acquire_time += timedelta(hours=1, minutes=45)

        base_url = run_time.strftime("https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/nam.%Y%m%d/nam.t%Hz.conusnest.hiresf{}.tm00.grib2")

        q = get_queue()
        for hr in range(time_min, time_max + 1):
            url = base_url.format(str(hr).zfill(2))
            q.put({
                "source": "nam",
                "valid_time": datetime2unix(run_time + timedelta(hours=hr)),
                "run_time": datetime2unix(run_time),
                "url": url,
                "idx_url": url+".idx",
            }, schedule_at=acquire_time)


if __name__ == "__main__":
    init_sentry()
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Ingest NAM')
    parser.add_argument('--offset', type=int, default=0, help='Run offset to ingest')
    args = parser.parse_args()

    run_time = datetime.utcnow()
    run_time = run_time.replace(hour=(run_time.hour//6)*6, minute=0, second=0, microsecond=0)
    run_time -= timedelta(hours=6*args.offset)
    NAM.queue(run_time=run_time)
