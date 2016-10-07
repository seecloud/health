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
from tests.unit import test

TEST_BUCKET = {
    'http_codes': {
        'buckets': [
            {'key': 123, 'doc_count': 1},
            {'key': 234, 'doc_count': 2},
            {'key': 345, 'doc_count': 3},
            {'key': 456, 'doc_count': 4},
            {'key': 567, 'doc_count': 5}
        ]},
    'doc_count': 15,
    'http_response_time_stats': {'sum_of_squares': 'fake'},
    'http_response_size_stats': {'sum_of_squares': 'fake'},
    'http_response_time_percentiles': {'values': {'50.0': 1,
                                                  '95.0': 2,
                                                  '99.0': 3}},
    'http_response_size_percentiles': {'values': {'50.0': 4,
                                                  '95.0': 5,
                                                  '99.0': 6}},
    'key_as_string': 'fake-timestamp',
    'key': 'fake-service',
    'services': {'buckets': []}
}
TEST_EXPECTED_RECORD = {
    'fci': 10.0 / 15.0,
    'http_codes': {'1xx': 1, '2xx': 2, '3xx': 3, '4xx': 4, '5xx': 5},
    'requests_count': 15,
    'response_size': {'50th': 4, '95th': 5, '99th': 6},
    'response_time': {'50th': 1, '95th': 2, '99th': 3},
    'service': 'fake-service',
    'timestamp': 'fake-timestamp'
}


class GetRequestTestCase(test.TestCase):
    def test_range_in_filters(self):
        self.assertIn({'range': {'Timestamp': 'fake-range'}},
                      driver.get_request('fake-range')['query']['filtered']
                      ['filter']['and']['filters'])


class TransformHTTPCodesTestCase(test.TestCase):
    def test_transform(self):
        buckets = [{'key': 123, 'doc_count': 1},
                   {'key': 234, 'doc_count': 2},
                   {'key': 345, 'doc_count': 3},
                   {'key': 456, 'doc_count': 4},
                   {'key': 567, 'doc_count': 5}]
        self.assertEqual({"1xx": 1, "2xx": 2, "3xx": 3, "4xx": 4, "5xx": 5},
                         driver.transform_http_codes(buckets))


class FCITestCase(test.TestCase):
    def test_no_codes(self):
        self.assertEqual(1.0, driver.fci({}))

    def test_fci(self):
        http_codes = {"1xx": 1, "2xx": 2, "3xx": 3, "4xx": 4, "5xx": 5}
        self.assertEqual(10.0 / 15.0, driver.fci(http_codes))


class RecordFromBucketTestCase(test.TestCase):
    def test_make_record(self):
        bucket = copy.deepcopy(TEST_BUCKET)
        ts = bucket['key_as_string']
        self.assertEqual(TEST_EXPECTED_RECORD,
                         driver.record_from_bucket(bucket, ts,
                                                   'fake-service'))


class MainTestCase(test.TestCase):
    def setUp(self):
        super(MainTestCase, self).setUp()
        self.request = self.mock_request()

    def prepare(self, latest_aggregated_ts=None):
        ts1 = latest_aggregated_ts or '2000-01-01T01:01:01'
        ts2 = '2000-01-09T01:01:01'
        days = utils.distance_in_days(ts1, ts2)
        responses = []
        resp = mock.Mock()
        resp.json.return_value = {
            'hits': {
                'total': 1,
                'hits': [{
                    '_source': {
                        'Timestamp': ts1
                    }
                }]
            }
        }
        responses.append(resp)
        resp = mock.Mock()
        resp.json.return_value = {
            'hits': {
                'hits': [{
                    '_source': {
                        'Timestamp': ts2
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
                bucket_key = 'interval%d:bucket%d' % (i, b)
                bucket = copy.deepcopy(TEST_BUCKET)
                bucket['key_as_string'] = bucket_key
                buckets.append(bucket)

                bucket_rec = copy.deepcopy(TEST_EXPECTED_RECORD)
                bucket_rec['timestamp'] = bucket_key
                bucket_rec['service'] = 'all'
                records.append(bucket_rec)

                for s in range(2):
                    service = copy.deepcopy(TEST_BUCKET)
                    service_key = 'interval%d:bucket%d:service%d' % (i, b, s)
                    service['key'] = service_key
                    bucket['services']['buckets'].append(service)

                    service_rec = copy.deepcopy(TEST_EXPECTED_RECORD)
                    service_rec['timestamp'] = bucket_key
                    service_rec['service'] = service_key
                    records.append(service_rec)
            expected_results.append(records)
            resp = mock.Mock()
            resp.json.return_value = {'aggregations': {'per_minute': {
                'buckets': buckets}}}
            responses.append(resp)
        self.request.side_effect = responses
        return expected_results, len(responses)

    def test_main(self, aggregated_ts=None):
        expected_results, expected_call_count = self.prepare(aggregated_ts)
        for i, res in enumerate(driver.main('fake-es', aggregated_ts)):
            self.assertEqual(expected_results[i], res)
        self.assertEqual(expected_call_count, self.request.call_count)

    def test_main_with_latest_aggregated_ts(self):
        self.test_main('2000-01-05T01:01:01')
