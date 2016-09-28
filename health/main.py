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

import json
import sys
import time
import traceback

import jsonschema
import requests
import schedule

from health.drivers import utils
from health.drivers.tcp import driver as tcp_driver
from health.mapping import es


CONF_PATH = "/etc/health/config.json"
CONF_SCHEMA = {
    "type": "object",
    "$schema": "http://json-schema.org/draft-04/schema",
    "properties": {
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string"
                    },
                    "driver": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "elastic_src": {"type": "string"}
                        },
                        "required": ["type", "elastic_src"]
                    }
                },
                "required": ["region", "driver"]
            }
        },
        "backend": {
            "type": "object",
            "properties": {
                "elastic": {
                    "type": "string"
                }
            },
            "required": ["elastic"]
        },
        "config": {
            "type": "object",
            "properties": {
                "run_every_minutes": {
                    "type": "integer",
                    "minimum": 1
                }
            }
        }
    },
    "additionalProperties": False
}


CONF = None


def job():
    backend_url = "%s/ms_health/service" % CONF["backend"]["elastic"]

    min_ts, max_ts = utils.get_min_max_timestamps(backend_url, "timestamp")

    for src in CONF["sources"]:
        # TODO(boris-42): Make this actually pluggable
        data_generator = tcp_driver.main(src["driver"]["elastic_src"],
                                         latest_aggregated_ts=max_ts)

        print("Fetching data from %s region" % src["region"])

        for i, data_interval in enumerate(data_generator):
            print("Fetching data from %s region, chunk %s"
                  % (src["region"], i))

            if not data_interval:
                print("Region %s is already synced." % src["region"])
                return

            req_data = []
            for d in data_interval:
                d["region"] = src["region"]
                # TODO(boris-42): Data is validated only by ES, which is bad
                req_data.append('{"index": {}}')
                req_data.append(json.dumps(d))
            req_data = "\n".join(req_data)
            print("Posting data to elastic %s" % i)
            r = requests.post("%s/_bulk" % backend_url, data=req_data)


def main():
    global CONF
    try:
        with open(CONF_PATH) as f:
            CONF = json.load(f)
            jsonschema.validate(CONF, CONF_SCHEMA)

    except (OSError, IOError):
        print("Sorry, couldn't open configuration file: %s" % CONF_PATH)
        traceback.print_exc()
        sys.exit(1)
    except jsonschema.ValidationError as e:
        print(e.message)
        sys.exit(1)
    except jsonschema.SchemaError as e:
        print(e)
        sys.exit(1)
    else:
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
