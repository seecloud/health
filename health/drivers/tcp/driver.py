#!/usr/bin/python

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

import copy
import json


from health.drivers import utils
import requests




STATS = {
    "http_response_time_stats": {
        "extended_stats": {
            "field": "http_response_time"
        }
    },
    "http_response_time_percentiles": {
        "percentiles": {
            "field": "http_response_time"
        }
    },
    "http_response_size_stats": {
        "extended_stats": {
            "field": "http_response_size"
        }
    },
    "http_response_size_percentiles": {
        "percentiles": {
            "field": "http_response_size"
        }
    }
}


AGG_REQUEST = {
    "query": {
        "filtered": {
            "filter": {
                "and": {
                    "filters": [
                      {"exists": {"field": "http_method"}},
                      {"exists": {"field": "http_status"}},
                      {"exists": {"field": "http_response_time"}}
                    ]
                }
            }
        }
    },
    "aggs": {
        "per_minute": {
            "date_histogram": {
                "field": "Timestamp",
                "interval": "minute",
                "format": "yyyy-MM-dd'T'hh:mm:ss",
                "min_doc_count": 0
            },
            "aggs": {
                "http_codes": {
                    "terms": {
                        "field": "http_status"
                    }
                },
                "services": {
                    "terms": {
                        "field": "Logger"
                    },
                    "aggs": {
                        "http_codes": {
                            "terms": {
                                "field": "http_status"
                            }
                        }
                    }
                }
            }
        }
    }
}


AGG_REQUEST["aggs"]["per_minute"]["aggs"].update(STATS)
AGG_REQUEST["aggs"]["per_minute"]["aggs"]["services"]["aggs"].update(STATS)


def get_request(ts_range):
    query = copy.deepcopy(AGG_REQUEST)
    query["query"]["filtered"]["filter"]["and"]["filters"].append({
        "range": {"Timestamp": ts_range}
    })
    return query


def transform_http_codes(buckets):
    result = {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}

    for b in buckets:
        result["%sxx" % (int(b["key"]) // 100)] = b["doc_count"]
    return result


def fci(http_codes):
    all_codes = sum(v for k, v in http_codes.items())
    return float((all_codes - http_codes["5xx"])) / all_codes


def record_from_bucket(bucket, timestamp, service):
    http_codes = transform_http_codes(bucket["http_codes"]["buckets"])
    record = {
        "timestamp": timestamp,
        "requests_count": bucket["doc_count"],
        "service": service,
        "fci": fci(http_codes),
        "http_codes": http_codes,
        "response_time": bucket["http_response_time_stats"],
        "response_size": bucket["http_response_size_stats"]
    }

    del record["response_time"]["sum_of_squares"]
    del record["response_size"]["sum_of_squares"]

    for el in ["response_time", "response_size"]:
        for pth in ["50.0", "95.0", "99.0"]:
            value = bucket["http_%s_percentiles" % el]["values"][pth]
            record[el]["%sth" % pth[:-2]] = value

    return record


def main(es, latest_aggregated_ts=None):
    ts_min, ts_max = utils.get_min_max_timestamps(es, "Timestamp")

    if latest_aggregated_ts:
        intervals = utils.incremental_scan(ts_max, latest_aggregated_ts)
    else:
        intervals = utils.incremental_scan(ts_max, ts_min)

    for interval in intervals:
        body = get_request(interval)
        resp = requests.post("%s/_search?search_type=count" % es,
                             data=json.dumps(body)).json()

        print(resp)

        r = []
        for bucket in resp["aggregations"]["per_minute"]["buckets"]:

            ts = bucket["key_as_string"]
            r.append(record_from_bucket(bucket, ts, "all"))

            for service in bucket["services"]["buckets"]:
                r.append(record_from_bucket(service, ts, service["key"]))
        yield r

