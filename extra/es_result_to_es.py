#!/usr/bin/env python

import json
import sys

import requests


def main():
    bulk = []

    with open(sys.argv[1]) as f:
        for hit in json.load(f)["hits"]["hits"]:
            bulk.append('{ "index": {}}')
            bulk.append(json.dumps(hit["_source"]))

    print(len(bulk))
    bulk = "\n".join(bulk)

    requests.post(sys.argv[2], data=bulk)


if __name__ == "__main__":
    main()
