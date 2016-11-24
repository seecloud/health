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

import mock

from health.drivers import utils
from tests.unit import test  # noqa


class DistanceInDaysTestCase(test.TestCase):
    def test_direct_order(self):
        ts1 = "2000-01-01T01:01:01"
        ts2 = "2000-01-06T01:01:01"
        self.assertEqual(5, utils.distance_in_days(ts1, ts2))

    def test_reverse_order(self):
        ts1 = "2000-01-01T01:01:01"
        ts2 = "2000-01-06T01:01:01"
        self.assertEqual(5, utils.distance_in_days(ts2, ts1))


class GetMinMaxTimestampTestCase(test.TestCase):
    def setUp(self):
        super(GetMinMaxTimestampTestCase, self).setUp()
        self.request = self.mock_request()

    def test_zero_total_hits_of_min(self):
        self.request.return_value.json.return_value = {"hits": {"total": 0}}
        self.assertEqual([None, None],
                         utils.get_min_max_timestamps("fake-se", "fake-field"))
        self.request.assert_called_once_with(
            "get", "fake-se/_search?size=1", allow_redirects=True,
            data='{"sort": {"fake-field": {"order": "asc"}}}', params=None)

    def test_non_zero_total_hits_of_min(self):
        r1 = mock.Mock()
        r1.json.return_value = {
            "hits": {
                "total": 1,
                "hits": [{
                    "_source": {
                        "fake-field": "fake-1"
                    }
                }]
            }
        }
        r2 = mock.Mock()
        r2.json.return_value = {
            "hits": {
                "hits": [{
                    "_source": {
                        "fake-field": "fake-2"
                    }
                }]
            }
        }
        self.request.side_effect = [r1, r2]
        self.assertEqual(["fake-1", "fake-2"],
                         utils.get_min_max_timestamps("fake-se", "fake-field"))
        self.assertEqual(2, self.request.call_count)
        calls = [mock.call("get", "fake-se/_search?size=1",
                           allow_redirects=True,
                           data='{"sort": {"fake-field": {"order": "asc"}}}',
                           params=None),
                 mock.call("get", "fake-se/_search?size=1",
                           allow_redirects=True,
                           data='{"sort": {"fake-field": {"order": "desc"}}}',
                           params=None)]
        self.request.assert_has_calls(calls)


class IncrementalScanTestCase(test.TestCase):
    def test_zero_days(self):
        max_ts = "2000-01-01T01:01:01"
        current_ts = "2000-01-01T01:01:01"
        self.assertEqual([{"gte": "2000-01-01T01:01:01||+1m/m",
                           "lt": "2000-01-01T01:01:01||/m"}],
                         utils.incremental_scan(max_ts, current_ts))

    def test_non_zero_days(self):
        max_ts = "2000-01-02T01:01:01"
        current_ts = "2000-01-01T01:01:01"
        self.assertEqual([{"gte": "2000-01-01T01:01:01||+1m+0d/m",
                           "lt": "2000-01-01T01:01:01||+1m+1d/m"},
                          {"gte": "2000-01-01T01:01:01||+1m+1d/m",
                           "lt": "2000-01-02T01:01:01||/m"}],
                         utils.incremental_scan(max_ts, current_ts))
