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

import flask
import requests


regions = flask.Blueprint("regions", __name__)


def get_blueprints():
    return [
        ["/regions", regions],
    ]


@regions.route("/")
def get_regions():

    query = {
        "size": 0,
        "aggs": {
            "regions": {
                "terms": {"field": "region"}
            }
        }
    }
    request = flask.current_app.config["backend"]["elastic"]
    r = requests.get("%s/_search" % request,
                     data=json.dumps(query))

    if not r.ok:
        print("Got {} status when requesting {}. {}".format(request, r.text))
        raise RuntimeError(r.text)

    buckets = r.json()["aggregations"]["regions"]["buckets"]
    regions = [bucket["key"] for bucket in buckets]

    return flask.jsonify(regions)
