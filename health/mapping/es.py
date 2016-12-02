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
import sys

import requests

_http_codes = {
    "type": "object",
    "properties": {
        "1xx": {"type": "integer"},
        "2xx": {"type": "integer"},
        "3xx": {"type": "integer"},
        "4xx": {"type": "integer"},
        "5xx": {"type": "integer"}
    }
}

_stats = {
    "type": "object",
    "properties": {
        "min": {"type": "float"},
        "avg": {"type": "float"},
        "max": {"type": "float"},
        "sum": {"type": "float"},
        "variance": {"type": "float"},
        "std_deviation": {"type": "float"},
        "std_deviation_bounds": {
            "type": "object",
            "properties": {
                "upper": {"type": "float", "index": "no"},
                "lower": {"type": "float", "index": "no"}
            }
        },
        "50th": {"type": "float"},
        "95th": {"type": "float"},
        "99th": {"type": "float"}
    }
}

mapping = {
    "settings": {
        "number_of_shards": 5
    },
    "aliases": {
        "ms_health": {}
    },
    "mappings": {
        "service": {
            "_all": {"enabled": False},
            "properties": {
                "timestamp": {"type": "date"},
                "service": {"type": "keyword"},
                "region": {"type": "keyword"},
                "requests_count": {"type": "integer"},
                "fci": {"type": "float"},
                "http_codes": _http_codes,
                "response_time": _stats,
                "response_size": _stats
            }
        }
    }
}


def init_elastic(es, index_to_create="ms_health_idx_1"):
    r = requests.get("%s/%s" % (es, index_to_create))

    if not r.ok:
        r = requests.put("%s/%s" % (es, index_to_create),
                         data=json.dumps(mapping))
        if r.ok:
            logging.info("Index '{}' created successfully".format(
                index_to_create))
        else:
            logging.error("Got {} status when creating index '{}'. {}".format(
                r.status_code, index_to_create, r.text))
            sys.exit(1)
    else:
        logging.info("Index {} already exists".format(index_to_create))
