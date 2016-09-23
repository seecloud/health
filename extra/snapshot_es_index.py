#!/usr/bin/env python

import json
import os
import sys
import traceback


import requests


CONF = {
    "ES": None,
    "INDEXES": None,
    "REPO_NAME": "log_backup",
    "REPO_PATH": "/mount/es_backup/",
    "DEBUG": False
}


def update_conf_from_env():
    for key in CONF:
        if key in os.environ:
            CONF[key] = os.environ[key]

    for key in CONF:
        if CONF[key] is None:
            raise Exception("You should pass %s env variable to script." % key)

    try:
        mappings = "/".join([CONF["ES"], CONF["INDEXES"], "_mapping"])
        r = requests.get(mappings)
    except:
        print("Can't connect to the ElasticSearch %s\n" % CONF["ES"])
        raise
    else:
        if r.status_code != 200:
            print("ElasticSearch URL or Indexes are wrong: %s" % mappings)
            print(json.dumps(r.json(), indent=4))
            raise Exception("ElasticSearch %s" % CONF["ES"])


def recreate_backup(backup_url, backup_path):
    if requests.get(backup_url).status_code == 200:
        requests.delete(backup_url)

    payload = {
        "type": "fs",
        "settings": {
            "compress": True,
            "location": backup_path
        }
    }
    r = requests.post(backup_url, data=json.dumps(payload))
    if r.status_code != 200:
        print("Can't create backup %s (%s)" % (backup_url, r.status_code))
        print(json.dumps(r.json(), indent=4))
        raise Exception("Can't create backup %s" % r)


def do_backup(backup_url, indexes):
    payload = {
        "indices": indexes,
        "ignore_unavailable": True,
        "include_global_state": False
    }
    requests.put("/".join([backup_url, "backup_1"]),
                 params={"wait_for_completion": True},
                 data=json.dumps(payload))


def main():
    try:
        update_conf_from_env()

        backup_url = "/".join([CONF["ES"], "_snapshot", CONF["REPO_NAME"]])

        recreate_backup(backup_url,
                        "/".join([CONF["REPO_PATH"], CONF["REPO_NAME"]]))
        do_backup(backup_url, CONF["INDEXES"])

    except Exception:
        print("Something went wrong, pass DEBUG=True to see exception.")
        if CONF["DEBUG"]:
            traceback.print_exc()

        sys.exit(1)


if __name__ == "__main__":
    main()
