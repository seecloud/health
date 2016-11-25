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
from werkzeug.contrib import cache


health = flask.Blueprint("health", __name__)


def get_blueprints():
    return [
        ["/health", health],
    ]


CACHE = cache.SimpleCache(threshold=50, default_timeout=30)


@health.route("/", defaults={"region": "all"})
@health.route("/<region>")
def get_health(region):

    period = flask.request.args.get("period", "day")

    result = CACHE.get("{}:{}".format(region, period))
    if result is not None:
        return flask.jsonify(**result)

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
            "projects": {
                "terms": {"field": "service"},

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
                                "avg": {"field": "response_time.avg"}
                            },
                            "response_time": {
                                "avg": {"field": "response_size.avg"}
                            }
                        }
                    }
                }
            }
        }
    }

    # only match if region is not "all"
    if region != "all":
        region = {
            "match": {"region": region}
        }
        query["query"]["bool"]["filter"].append(region)

    request = flask.current_app.config["backend"]["elastic"]
    r = requests.get("%s/_search" % request,
                     data=json.dumps(query))

    if not r.ok:
        logging.error("Got {} status when requesting {}. {}".format(
            request, r.text))
        raise RuntimeError(r.text)

    result = {
        "project_names": [],
        "projects": {}
    }

    def convert_(data, field):
        result = []
        for d in data["buckets"]:
            result.append([d["key_as_string"], d[field]["value"]])
        return result

    for project in r.json()["aggregations"]["projects"]["buckets"]:
        result["project_names"].append(project["key"])
        result["projects"][project["key"]] = {
            "fci": project["avg_fci"]["value"],
            "fci_score_data": convert_(project["data"], "fci"),
            "response_time_data": convert_(project["data"], "response_time"),
            "response_size_data": convert_(project["data"], "response_size")
        }

    CACHE.set("{}:{}".format(region, period), result)

    return flask.jsonify(**result)
