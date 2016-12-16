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

import logging
import sys

import elasticsearch

from health import config


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

ES_MAPPINGS = {
    "settings": {
        "number_of_shards": 5
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

ES_CLIENT = None


def get_elasticsearch():
    """Configures or returns already configured ES client."""
    global ES_CLIENT
    if not ES_CLIENT:
        nodes = config.get_config()["backend"]["connection"]
        ES_CLIENT = elasticsearch.Elasticsearch(nodes)
    return ES_CLIENT


EXISTING_INDICES = set()


def ensure_index_exists(region):
    index_to_create = "ms_health_%s" % region

    if index_to_create in EXISTING_INDICES:
        return

    es = get_elasticsearch()

    if not es.indices.exists(index_to_create):
        try:
            es.indices.create(index_to_create, ES_MAPPINGS)
            logging.info("Created '{}' index".format(index_to_create))
        except elasticsearch.ElasticsearchException as e:
            if e.error == "index_already_exists_exception":
                # we might catch already exists here if 2 jobs are strted
                # concurrently. It's ok.
                logging.info(
                    "Index {} already exists".format(index_to_create))
                EXISTING_INDICES.add(index_to_create)
            else:
                logging.error(
                    "Got {} error when creating index '{}'.".format(
                        e, index_to_create))
                sys.exit(1)
            EXISTING_INDICES.add(index_to_create)
    else:
        logging.info("Index {} already exists".format(index_to_create))
        EXISTING_INDICES.add(index_to_create)
