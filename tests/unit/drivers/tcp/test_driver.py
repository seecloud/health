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

import mock

from health.drivers.tcp import driver
from health.drivers import utils
from tests.unit import test  # noqa


TEST_BUCKET = {
    "http_codes": {
        "buckets": [
            {"key": 123, "doc_count": 1},
            {"key": 234, "doc_count": 2},
            {"key": 345, "doc_count": 3},
            {"key": 456, "doc_count": 4},
            {"key": 567, "doc_count": 5}
        ]},
    "doc_count": 15,
    "http_response_time_stats": {"sum_of_squares": "fake"},
    "http_response_size_stats": {"sum_of_squares": "fake"},
    "http_response_time_percentiles": {"values": {"50.0": 1,
                                                  "95.0": 2,
                                                  "99.0": 3}},
    "http_response_size_percentiles": {"values": {"50.0": 4,
                                                  "95.0": 5,
                                                  "99.0": 6}},
    "key_as_string": "fake-timestamp",
    "key": "fake-service",
    "services": {"buckets": []}
}


TEST_EXPECTED_RECORD = {
    "fci": 10.0 / 15.0,
    "http_codes": {"1xx": 1, "2xx": 2, "3xx": 3, "4xx": 4, "5xx": 5},
    "requests_count": 15,
    "response_size": {"50th": 4, "95th": 5, "99th": 6},
    "response_time": {"50th": 1, "95th": 2, "99th": 3},
    "service": "fake-service",
    "timestamp": "fake-timestamp"
}


class DriverTestCase(test.TestCase):

    def setUp(self):
        super(DriverTestCase, self).setUp()
        self.driver = driver.Driver({
            "elastic_src": "http://elastic:9200/log*/log"})

    @mock.patch("health.drivers.tcp.driver.requests.get")
    def test_get_request(self, mock_requests_get):
        self.driver.use_keyword = False
        self.assertIn(
            {"range": {"Timestamp": "fake-range"}},
            self.driver.get_request("fake-range")["query"]["bool"]["filter"])
        self.assertEqual(mock_requests_get.call_count, 0)

    @mock.patch("health.drivers.tcp.driver.requests.get")
    def test_get_request_use_keyword(self, mock_requests_get):
        mock_requests_get.return_value.json.return_value = {
            "index_name": {
                "mappings": {
                    "aaa": {
                        "properties": {
                            "Logger": {"fields": {"keyword": {}}}
                        }
                    }
                }
            }
        }
        self.driver.get_request("fake-range")
        self.assertTrue(self.driver.use_keyword)
        mock_requests_get.assert_called_once_with("http://elastic:9200/log*")

    @mock.patch("health.drivers.tcp.driver.requests.get")
    def test_get_request_dont_use_keyword(self, mock_requests_get):
        mock_requests_get.return_value.json.return_value = {
            "index_name": {
                "mappings": {
                    "aaa": {
                        "properties": {
                            "Logger": {"type": "text"}
                        }
                    }
                }
            }
        }
        self.driver.get_request("fake-range")
        self.assertFalse(self.driver.use_keyword)
        mock_requests_get.assert_called_once_with("http://elastic:9200/log*")

    def test_transform_http_codes(self):
        buckets = [{"key": 123, "doc_count": 1},
                   {"key": 234, "doc_count": 2},
                   {"key": 345, "doc_count": 3},
                   {"key": 456, "doc_count": 4},
                   {"key": 567, "doc_count": 5}]
        self.assertEqual({"1xx": 1, "2xx": 2, "3xx": 3, "4xx": 4, "5xx": 5},
                         self.driver.transform_http_codes(buckets))

    def test_fci(self):
        http_codes = {"1xx": 1, "2xx": 2, "3xx": 3, "4xx": 4, "5xx": 5}
        self.assertEqual(10.0 / 15.0, self.driver.fci(http_codes))

    def test_fci_no_codes(self):
        self.assertEqual(1.0, self.driver.fci({}))

    def test_record_from_bucket(self):
        bucket = copy.deepcopy(TEST_BUCKET)
        ts = bucket["key_as_string"]
        self.assertEqual(TEST_EXPECTED_RECORD,
                         self.driver.record_from_bucket(bucket, ts,
                                                        "fake-service"))

    def _prepare(self, mock_request, latest_aggregated_ts=None):
        ts1 = latest_aggregated_ts or "2000-01-01T01:01:01"
        ts2 = "2000-01-09T01:01:01"
        days = utils.distance_in_days(ts1, ts2)
        responses = []
        resp = mock.Mock()
        resp.json.return_value = {
            "hits": {
                "total": 1,
                "hits": [{
                    "_source": {
                        "Timestamp": ts1
                    }
                }]
            }
        }
        responses.append(resp)
        resp = mock.Mock()
        resp.json.return_value = {
            "hits": {
                "hits": [{
                    "_source": {
                        "Timestamp": ts2
                    }
                }]
            }
        }
        responses.append(resp)

        expected_results = []
        for i in range(days + 1):
            buckets = []
            records = []
            for b in range(2):
                bucket_key = "interval%d:bucket%d" % (i, b)
                bucket = copy.deepcopy(TEST_BUCKET)
                bucket["key_as_string"] = bucket_key
                buckets.append(bucket)

                bucket_rec = copy.deepcopy(TEST_EXPECTED_RECORD)
                bucket_rec["timestamp"] = bucket_key
                bucket_rec["service"] = "all"
                records.append(bucket_rec)

                for s in range(2):
                    service = copy.deepcopy(TEST_BUCKET)
                    service_key = "interval%d:bucket%d:service%d" % (i, b, s)
                    service["key"] = service_key
                    bucket["services"]["buckets"].append(service)

                    service_rec = copy.deepcopy(TEST_EXPECTED_RECORD)
                    service_rec["timestamp"] = bucket_key
                    service_rec["service"] = service_key
                    records.append(service_rec)
            expected_results.append(records)
            resp = mock.Mock()
            resp.json.return_value = {"aggregations": {"per_minute": {
                "buckets": buckets}}}
            responses.append(resp)
        mock_request.side_effect = responses
        return expected_results, len(responses)

    @mock.patch("requests.api.request")
    def test_fetch(self, mock_request, aggregated_ts=None):
        self.driver.use_keyword = False
        expected_results, expected_call_count = self._prepare(
            mock_request, aggregated_ts)
        for i, res in enumerate(self.driver.fetch(aggregated_ts)):
            self.assertEqual(expected_results[i], res)
        self.assertEqual(expected_call_count, mock_request.call_count)

    def test_fetch_with_latest_aggregated_ts(self):
        self.test_fetch(aggregated_ts="2000-01-05T01:01:01")
