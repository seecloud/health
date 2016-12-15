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
import logging

import flask
import requests

from health import config

health = flask.Blueprint("health", __name__)


def get_blueprints():
    return [
        ["", health],
    ]


def convert(data, field):
    result = []
    for d in data["buckets"]:
        result.append([d["key_as_string"], d[field]["value"]])
    return result


def get_period_interval(period):
    if period == "week":
        period = "now-7d/m"
        interval = "1h"
    elif period == "month":
        period = "now-30d/m"
        interval = "4h"
    else:
        # assuming day
        period = "now-1d/m"
        interval = "10m"
    return period, interval


def get_query(period, interval, aggs_name, aggs_term):

    query = {
        "size": 0,  # this is a count request
        "query": {
            "bool": {
                "filter": [{
                    "range": {
                        "timestamp": {
                            "gte": period
                        }
                    }
                }]
            }
        },
        "aggs": {
            aggs_name: {
                "terms": {"field": aggs_term},

                "aggs": {
                    "fci": {"avg": {"field": "fci"}},
                    "api_calls_count": {"sum": {"field": "requests_count"}},
                    "response_size": {"avg": {"field": "response_size.avg"}},
                    "response_time": {"avg": {"field": "response_time.avg"}},
                    "data": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": interval,
                            "format": "yyyy-MM-dd'T'HH:mm",
                            "min_doc_count": 0
                        },
                        "aggs": {
                            "fci": {
                                "avg": {"field": "fci"}
                            },
                            "api_count": {
                                "avg": {"field": "requests_count"}
                            },
                            "response_size": {
                                "avg": {"field": "response_size.sum"}
                            },
                            "response_time": {
                                "avg": {"field": "response_time.95th"}
                            }
                        }
                    }
                }
            }
        }
    }
    return query


@health.route("/region/<region>/health", defaults={"period": "day"})
@health.route("/region/<region>/health/<period>")
def get_health(region, period):

    if period not in ["day", "week", "month"]:
        flask.abort(404, "Unsupported period '{}'".format(period))

    period, interval = get_period_interval(period)

    query = get_query(period, interval,
                      aggs_name="projects", aggs_term="service")

    # only match if region is not "all"

    request = config.get_config()["backend"]["elastic"]
    r = requests.get("%s/ms_health_%s/_search" % (request, region),
                     data=json.dumps(query))

    if not r.ok:
        logging.error("Got {} status when requesting {}. {}".format(
            r.status_code, request, r.text))
        flask.abort(500, r.text)

    result = {
        "project_names": [],
        "health": {}
    }

    for project in r.json()["aggregations"]["projects"]["buckets"]:
        result["project_names"].append(project["key"])
        result["health"][project["key"]] = {
            "api_calls_count": project["api_calls_count"]["value"],
            "api_calls_count_data": convert(project["data"], "api_count"),
            "fci": project["fci"]["value"],
            "fci_data": convert(project["data"], "fci"),
            "response_size": project["response_size"]["value"],
            "response_time_data": convert(project["data"],
                                          "response_time"),
            "response_time": project["response_time"]["value"],
            "response_size_data": convert(project["data"],
                                          "response_size")
        }

    return flask.jsonify(**result)


@health.route("/health", defaults={"period": "day"})
@health.route("/health/<period>")
def get_overview(period):
    if period not in ["day", "week", "month"]:
        flask.abort(404, "Unsupported period '{}'".format(period))

    period, interval = get_period_interval(period)
    query = get_query(
        period, interval, aggs_name="regions", aggs_term="region")

    request = config.get_config()["backend"]["elastic"]
    r = requests.get("%s/ms_health_*/_search" % request,
                     data=json.dumps(query))

    if not r.ok:
        logging.error("Got {} status when requesting {}. {}".format(
            r.status_code, request, r.text))
        flask.abort(500, r.text)

    result = {
        "region_names": [],
        "health": {}
    }

    for region in r.json()["aggregations"]["regions"]["buckets"]:
        result["region_names"].append(region["key"])
        result["health"][region["key"]] = {
            "api_calls_count": region["api_calls_count"]["value"],
            "api_calls_count_data": convert(region["data"], "api_count"),
            "fci": region["fci"]["value"],
            "fci_data": convert(region["data"], "fci"),
            "response_size": region["response_size"]["value"],
            "response_time_data": convert(region["data"], "response_time"),
            "response_time": region["response_time"]["value"],
            "response_size_data": convert(region["data"], "response_size")
        }

    return flask.jsonify(**result)
