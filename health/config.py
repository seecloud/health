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

DEFAULT_CONF_PATH = "/etc/health/config.yaml"

DEFAULT = {
    "sources": [
        {
            "region": "region",
            "driver": {
                "type": "tcp",
                "elastic_src": "http://127.0.0.1:9200/log-*/log",
            },
        },
    ],
    "backend": {
        "elastic": "http://127.0.0.1:9200/",
    },
    "config": {
        "run_every_minutes": 2,
    },
}

SCHEMA = {
    "sources": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                },
                "driver": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "elastic_src": {"type": "string"},
                    },
                    "required": ["type", "elastic_src"],
                },
            },
            "required": ["region", "driver"],
            "additionalProperties": False,
        },
    },
    "backend": {
        "type": "object",
        "properties": {
            "elastic": {
                "type": "string"
            },
        },
        "required": ["elastic"],
        "additionalProperties": False,
    },
    "config": {
        "type": "object",
        "properties": {
            "run_every_minutes": {
                "type": "integer",
                "minimum": 1,
            },
        },
        "additionalProperties": False,
    },
}
