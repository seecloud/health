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

import json
import sys
import urlparse

import requests


def main():
    bulk = []

    if len(sys.argv) < 3:
        print("Usage:\n {} "
              "./tcp_log.json "
              "http://127.0.0.1:9200/".format(sys.argv[0]))
        sys.exit(1)

    FIELDS = ['_index', '_type', '_id']
    with open(sys.argv[1]) as f:
        for hit in json.load(f)["hits"]["hits"]:
            index_dct = {}

            for field in FIELDS:
                index_dct[field] = hit[field]
            bulk.append(json.dumps({"index": index_dct}))
            bulk.append(json.dumps(hit["_source"]))

    bulk = "\n".join(bulk)

    resp = requests.post(urlparse.urljoin(sys.argv[2], "_bulk"), data=bulk)
    if resp.ok:
        print("Successfully loaded data from {} to ElasticSearch".format(
            sys.argv[1]))
    else:
        print("Got a {} response from ElasticSearch".format(resp.status_code))
        print(resp.text)


if __name__ == "__main__":
    main()
