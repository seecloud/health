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

import requests
import schedule

from health import config
from health.drivers import utils
from health.mapping import es


LOGGING_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
logging.basicConfig(format=LOGGING_FORMAT, level=logging.INFO)


CONF = None


def _get_driver(driver_type):
    try:
        return importlib.import_module("." + driver_type + ".driver",
                                       "health.drivers").Driver
    except ImportError:
        logging.error("Could not load driver for '{}'".format(driver_type))
        raise


def ignore_exceptions(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error("Caught {} while running '{}' function".format(
                e, func.__name__))

    return wrapper


@ignore_exceptions
def job():
    started_at = time.time()
    logging.info("Starting Syncing Job")

    backend_url = "%s/ms_health/service" % CONF["backend"]["elastic"]

    min_ts, max_ts = utils.get_min_max_timestamps(backend_url, "timestamp")

    for src in CONF["sources"]:
        driver = _get_driver(src["driver"]["type"])(src["driver"])
        data_generator = driver.fetch(latest_aggregated_ts=max_ts)

        logging.info("Start syncing %s region" % src["region"])

        for i, data_interval in enumerate(data_generator):

            if not data_interval:
                logging.info("Chunk %s from region %s is already synced."
                             % (i, src["region"]))
                continue

            req_data = []
            for d in data_interval:
                d["region"] = src["region"]
                # TODO(boris-42): Data is validated only by ES, which is bad
                req_data.append('{"index": {}}')
                req_data.append(json.dumps(d))
            req_data = "\n".join(req_data)
            logging.info("Sending data from chunk {} to backend".format(i))

            try:
                r = requests.post("%s/_bulk" % backend_url, data=req_data)
            except requests.exceptions.RequestException:
                logging.error("Was unable to store data for {} "
                              "Stopping current job run".format(
                                  data_interval))
                break
            logging.debug(r.text)

    logging.info("Syncing job completed in %.3f seconds"
                 % (time.time() - started_at))


def main():
    global CONF
    CONF = config.get_config()
    # Init Elastic index in backend
    es.init_elastic(CONF["backend"]["elastic"])

    # Setup periodic job that does aggregation magic
    run_every_min = CONF.get("config", {}).get("run_every_minutes", 1)
    schedule.every(run_every_min).minutes.do(job)

    job()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
