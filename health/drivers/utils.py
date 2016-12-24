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
import logging

import requests

LOG = logging.getLogger(__name__)

TS_FMT = "%Y-%m-%dT%H:%M:%S"


def distance_in_days(ts1, ts2):
    ts1, ts2 = sorted([datetime.datetime.strptime(ts1, TS_FMT),
                       datetime.datetime.strptime(ts2, TS_FMT)])

    return int(round((ts2 - ts1).total_seconds() / 3600 / 24))


def get_min_max_timestamps(es, field):
    url = "%s/_search?size=1" % es

    r_min = requests.get(
        url, data=json.dumps({"sort": {field: {"order": "asc"}}}))

    if not r_min.ok:
        LOG.error(
            "Got %s status when requesting %s, assuming empty intervals: %s",
            r_min.status_code, url, r_min.text)
        return [None, None]

    if r_min.json()["hits"]["total"] == 0:
        return [None, None]

    r_max = requests.get(
        url, data=json.dumps({"sort": {field: {"order": "desc"}}}))

    return [el.json()["hits"]["hits"][0]["_source"][field]
            for el in [r_min, r_max]]


def incremental_scan(max_ts, current_ts):
    days = distance_in_days(max_ts, current_ts)
    intervals = []

    if days == 0:
        return [{
            "gte": "%s||+1m/m" % current_ts,
            "lt": "%s||/m" % max_ts
        }]

    intervals = []
    for day in range(days + 1):
        intervals.append({
            "gte": "%(ts)s||+1m+%(d)sd/m" % {"ts": current_ts, "d": day},
            "lt": "%(ts)s||+1m+%(d)sd/m" % {"ts": current_ts, "d": day + 1}
        })

    intervals[-1]["lt"] = "%s||/m" % max_ts
    return intervals
