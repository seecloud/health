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

import mock
from oss_lib import config

from tests.unit.api.v1 import base

CONF = config.CONF


class RegionsTestCase(base.APITestCase):
    services = [
        "all",
        "openstack.keystone",
        "openstack.nova",
        "openstack.glance",
    ]

    def _mock_response(self, mock_request, buckets=None, aggs_name="projects"):
        if buckets is None:
            buckets = self.services
        service_buckets = []
        for serv in self.services:
            inner_bucket = {
                "fci": {"value": 1.0},
                "api_calls_count": {"value": 4318.0},
                "data": {
                    "buckets": [{
                        "doc_count": 3,
                        "fci": {"value": 1.0},
                        "api_count": {"value": 431.0},
                        "key": 1474617600000,
                        "key_as_string": "2016-09-23T08:00",
                        "response_size": {"value": 0.025731437529126804},
                        "response_time": {"value": 5736.745768229167},
                    }]
                },
                "doc_count": 3,
                "key": serv,
                "response_size": {"value": 0.025731437529126804},
                "response_time": {"value": 5736.745768229167},
            }

            service_buckets.append(inner_bucket)

        response = {
            "aggregations": {
                aggs_name: {
                    "buckets": service_buckets,
                    "doc_count_error_upper_bound": 0,
                    "sum_other_doc_count": 0
                }
            },
            "hits": {"hits": [], "max_score": 0.0, "total": 14},
            "timed_out": False,
            "took": 23
        }
        resp = mock.Mock()
        resp.json.return_value = response
        mock_request.side_effect = [resp]

    @mock.patch("requests.api.request")
    def test_get_health(self, mock_request):
        self._mock_response(mock_request)

        resp = self.client.get("/api/v1/region/regionOne/health")
        resp_json = json.loads(resp.data.decode())
        self.assertEqual(200, resp.status_code)
        self.assertEqual(set(self.services), set(resp_json["project_names"]))
        self.assertEqual(set(self.services), set(resp_json["health"].keys()))

        request_args, request_kwargs = mock_request.call_args
        self.assertEqual(
            ("get", CONF["backend"]["elastic"] +
                "/ms_health_regionOne/_search"),
            request_args)
        data_requested = json.loads(request_kwargs["data"])
        expected_filter = [{
            "range": {
                "timestamp": {
                    "gte": "now-1d/m"
                }
            }
        }]
        self.assertEqual(expected_filter,
                         data_requested["query"]["bool"]["filter"])

    @mock.patch("requests.api.request")
    def test_get_health_period(self, mock_request):
        self._mock_response(mock_request)

        resp = self.client.get("/api/v1/region/regionOne/health/week")
        self.assertEqual(200, resp.status_code)

        request_args, request_kwargs = mock_request.call_args
        self.assertEqual(
            ("get", CONF["backend"]["elastic"] +
                "/ms_health_regionOne/_search"),
            request_args)
        data_requested = json.loads(request_kwargs["data"])
        expected_filter = [{
            "range": {
                "timestamp": {
                    "gte": "now-7d/m"
                }
            }
        }]
        self.assertEqual(expected_filter,
                         data_requested["query"]["bool"]["filter"])

    @mock.patch("requests.api.request")
    def test_get_health_all_regions(self, mock_request):
        self._mock_response(mock_request,
                            buckets=["regOne", "regTwo"], aggs_name="regions")

        resp = self.client.get("/api/v1/health")
        self.assertEqual(200, resp.status_code)

        resp_json = json.loads(resp.data.decode())
        self.assertEqual(set(self.services), set(resp_json["region_names"]))
        self.assertEqual(set(self.services), set(resp_json["health"].keys()))

        request_args, request_kwargs = mock_request.call_args
        self.assertEqual(
            ("get", CONF["backend"]["elastic"] +
                "/ms_health_*/_search"),
            request_args)
        data_requested = json.loads(request_kwargs["data"])
        expected_filter = [{
            "range": {
                "timestamp": {
                    "gte": "now-1d/m"
                }
            }
        }]
        self.assertEqual(expected_filter,
                         data_requested["query"]["bool"]["filter"])
