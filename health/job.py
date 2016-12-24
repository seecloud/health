# Copyright 2016: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import functools
import importlib
import json
import logging
import time

from oss_lib import config
import requests
import schedule

from health import config as cfg
from health.drivers import utils
from health.mapping import es

LOG = logging.getLogger(__name__)
CONF = config.CONF


def _get_driver(driver_type):
    try:
        return importlib.import_module("." + driver_type + ".driver",
                                       "health.drivers").Driver
    except ImportError:
        LOG.error("Could not load driver for '%s'", driver_type)
        raise


def ignore_exceptions(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            LOG.error("Caught %s while running '%s' function",
                      e, func.__name__)

    return wrapper


@ignore_exceptions
def job():
    started_at = time.time()
    LOG.info("Starting Syncing Job")

    for src in CONF["sources"]:
        backend_url = "%s/ms_health_%s/service" % (
            CONF["backend"]["elastic"], src["region"])
        min_ts, max_ts = utils.get_min_max_timestamps(backend_url, "timestamp")

        driver = _get_driver(src["driver"]["type"])(src["driver"])
        data_generator = driver.fetch(latest_aggregated_ts=max_ts)

        LOG.info("Start syncing %s region", src["region"])

        for i, data_interval in enumerate(data_generator):

            if not data_interval:
                LOG.info("Chunk %s from region %s is already synced.",
                         i, src["region"])
                continue

            req_data = []
            for d in data_interval:
                d["region"] = src["region"]
                # TODO(boris-42): Data is validated only by ES, which is bad
                req_data.append('{"index": {}}')
                req_data.append(json.dumps(d))
            req_data = "\n".join(req_data)
            LOG.info("Sending data from chunk %s to backend", i)

            try:
                r = requests.post("%s/_bulk" % backend_url, data=req_data)
            except requests.exceptions.RequestException:
                LOG.error("Was unable to store data for %s Stopping current "
                          "job run", data_interval)
                break
            LOG.debug(r.text)

    LOG.info("Syncing job completed in %.3f seconds",
             (time.time() - started_at))


def main():
    config.process_args("HEALTH",
                        default_config_path=cfg.DEFAULT_CONF_PATH,
                        defaults=cfg.DEFAULT,
                        validation_schema=cfg.SCHEMA)
    # Init Elastic index in backend

    for src in CONF["sources"]:
        es.ensure_index_exists(CONF["backend"]["elastic"], src["region"])

    # Setup periodic job that does aggregation magic
    run_every_min = CONF["config"]["run_every_minutes"]
    schedule.every(run_every_min).minutes.do(job)

    job()

    while True:
        schedule.run_pending()
        time.sleep(1)
