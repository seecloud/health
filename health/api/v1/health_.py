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
    elif period == "year":
        period = "now-365d/m"
        interval = "8h"
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
                    "avg_fci": {
                        "avg": {
                            "field": "fci"
                        }
                    },
                    "data": {
                        "date_histogram": {
                            "field": "timestamp",
                            "interval": interval,
                            "format": "yyyy-MM-dd'T'hh:mm",
                            "min_doc_count": 0
                        },
                        "aggs": {
                            "fci": {
                                "avg": {"field": "fci"}
                            },
                            "response_size": {
                                "sum": {"field": "response_size.sum"}
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

    period, interval = get_period_interval(period)

    query = get_query(
        period, interval, aggs_name="projects", aggs_term="service")

    # only match if region is not "all"
    if region != "all":
        region = {
            "match": {"region": region}
        }
        query["query"]["bool"]["filter"].append(region)

    request = config.get_config()["backend"]["elastic"]
    r = requests.get("%s/_search" % request, data=json.dumps(query))

    if not r.ok:
        logging.error("Got {} status when requesting {}. {}".format(
            request, r.text))
        flask.abort(500, r.text)

    result = {
        "project_names": [],
        "projects": {}
    }

    for project in r.json()["aggregations"]["projects"]["buckets"]:
        result["project_names"].append(project["key"])
        result["projects"][project["key"]] = {
            "fci": project["avg_fci"]["value"],
            "fci_score_data": convert(project["data"], "fci"),
            "response_time_data": convert(project["data"],
                                          "response_time"),
            "response_size_data": convert(project["data"],
                                          "response_size")
        }

    return flask.jsonify(**result)


@health.route("/health", defaults={"period": "day"})
@health.route("/health/<period>")
def get_overview(period):

    period, interval = get_period_interval(period)
    query = get_query(
        period, interval, aggs_name="regions", aggs_term="region")

    request = config.get_config()["backend"]["elastic"]
    r = requests.get("%s/_search" % request, data=json.dumps(query))

    if not r.ok:
        logging.error("Got {} status when requesting {}. {}".format(
            request, r.text))
        flask.abort(500, r.text)

    result = {
        "region_names": [],
        "regions": {}
    }

    for region in r.json()["aggregations"]["regions"]["buckets"]:
        result["region_names"].append(region["key"])
        result["regions"][region["key"]] = {
            "fci": region["avg_fci"]["value"],
            "fci_score_data": convert(region["data"], "fci"),
            "response_time_data": convert(region["data"],
                                          "response_time"),
            "response_size_data": convert(region["data"],
                                          "response_size")
        }

    return flask.jsonify(**result)
