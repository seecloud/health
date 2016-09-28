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

import datetime
import json

import requests

request = []
URL = "http://172.16.5.147:9200/test/ts"


DAYS = 5
HOURS = 1
MIN = 1
SECONDS = 1


FMT = "%Y-%m-%dT%H:%M:%S"


def generate_request():
    for day in range(1, DAYS):
        for hour in range(24):
            for m in range(60):
                for s in range(60):
                    for repeat in range(SECONDS):
                        d = datetime.datetime(2016, 5, day, hour, m, s)
                        body = {"date": datetime.datetime.strftime(d, FMT)}
                        request.append('{ "index": {}}')
                        request.append(json.dumps(body))

    return "\n".join(request)


def main():
    print("Generating body ...")
    body = generate_request()
    print("Posting to ES")
    requests.post("%s/_bulk" % URL, data=body)
    print("Done!")


if __name__ == "__main__":
    main()
