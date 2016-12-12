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
import os
import sys

import jsonschema


CONF = None
DEFAULT_CONF = {
    "flask": {
        "HOST": "0.0.0.0",
        "PORT": 5000,
        "DEBUG": False
    },
    "sources": [
        {
            "region": "region",
            "driver": {
                "type": "tcp",
                "elastic_src": "http://127.0.0.1:9200/log-*/log"
            }
        }
    ],
    "backend": {
        "elastic": "http://127.0.0.1:9200/",
    },
    "config": {
        "run_every_minutes": 2
    }
}

CONF_SCHEMA = {
    "type": "object",
    "$schema": "http://json-schema.org/draft-04/schema",
    "properties": {
        "flask": {
            "type": "object"
        },
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


def get_config():
    """Return cached configuration.

    :returns: application config
    :rtype: dict
    """
    global CONF
    if not CONF:
        path = os.environ.get("HEALTH_CONF", "/etc/health/config.json")
        try:
            CONF = json.load(open(path))
            logging.info("Config is '%s'" % path)
        except IOError as e:
            logging.warning("Config at '%s': %s" % (path, e))
            CONF = DEFAULT_CONF
    try:
        jsonschema.validate(CONF, CONF_SCHEMA)
    except jsonschema.ValidationError as e:
        logging.error(e.message)
        sys.exit(1)
    except jsonschema.SchemaError as e:
        logging.error(e)
        sys.exit(1)
    else:
        return CONF
