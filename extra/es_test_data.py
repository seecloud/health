#!/usr/bin/env python

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

import datetime
import json
import sys

import requests


regions = {
    "west-1.hooli": ["all", "nova", "glance", "cinder"],
    "west-2.hooli": ["all", "keystone", "murano", "cinder"]
}


def gen_records(total_minutes=5):
    end = datetime.datetime.now()
    end -= datetime.timedelta(0, end.second, end.microsecond)
    one_minute = datetime.timedelta(0, 60)

    bulk = {}
    index = json.dumps({"index": {}})

    record = {
        "http_codes": {"3xx": 133, "2xx": 1308, "1xx": 0, "5xx": 0, "4xx": 0},
        "service": "all",
        "timestamp": "2016-09-23T11:22:00",
        "region": "region_1",
        "requests_count": 1441,
        "response_size": {
            "count": 1441,
            "95th": 6851.0,
            "min": 135.0,
            "max": 49615.0,
            "sum": 4728703.0,
            "50th": 889.0,
            "std_deviation": 3550.077843329984,
            "std_deviation_bounds": {
                "upper": 10381.698365355318, "lower": -3818.6130079646173},
            "variance": 12603052.69370247,
            "avg": 3281.5426786953503,
            "99th": 6851.0},
        "fci": 1.0,
        "response_time": {
            "count": 1441,
            "95th": 0.4180383582909902,
            "min": 0.0002629999944474548,
            "max": 1.4423577785491943,
            "sum": 116.91836558966315,
            "50th": 0.02351568154854216,
            "std_deviation": 0.14047865713532595,
            "std_deviation_bounds": {
                "upper": 0.36209427859380466, "lower": -0.19982034994749914},
            "variance": 0.019734253110544466,
            "avg": 0.08113696432315277,
            "99th": 0.5444556713104247
        }
    }

    for i in xrange(total_minutes):
        for region in regions:
            for service in regions[region]:
                key = "{r}/{s}".format(r=region, s=service)
                bulk.setdefault(key, [])
                record["region"] = region
                record["service"] = service
                record["timestamp"] = end.isoformat()
                bulk[key].append("{idx}\n{data}"
                                 .format(idx=index, data=json.dumps(record)))

        end -= one_minute

    print("Generated {chunks} chunks with {records} records"
          .format(chunks=len(bulk), records=len(bulk[bulk.keys()[0]])))

    results = []
    for key in bulk:
        bulk[key].append("")  # one blank at the end required
        results.append("\n".join(bulk[key]))

    return results


def populate_es(es, records):
    for i, record in enumerate(records):
        resp = requests.post("/".join([es, "_bulk"]), data=record)
        if resp.ok:
            print("Successfully uploaded data to ElasticSearch {es} {i}/{all}"
                  .format(es=es, i=i + 1, all=len(records)))
        else:
            print("Got a {} response from ElasticSearch"
                  .format(resp.status_code))
            print(resp.text)


def main():
    es = sys.argv[1]
    records = gen_records()
    populate_es(es, records)


if __name__ == "__main__":
    main()
