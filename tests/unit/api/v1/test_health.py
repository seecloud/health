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

from tests.unit.api.v1 import base


class RegionsTestCase(base.APITestCase):
    services = [
        "all",
        "openstack.keystone",
        "openstack.nova",
        "openstack.glance",
    ]

    def _mock_response(self):
        service_buckets = []
        for serv in self.services:
            inner_bucket = {
                "avg_fci": {"value": 1.0},
                "data": {
                    "buckets": [{
                        "doc_count": 3,
                        "fci": {"value": 1.0},
                        "key": 1474617600000,
                        "key_as_string": "2016-09-23T08:00",
                        "response_size": {"value": 0.025731437529126804},
                        "response_time": {"value": 5736.745768229167}
                    }]
                },
                "doc_count": 3,
                "key": serv,
            }

            service_buckets.append(inner_bucket)

        response = {
            "aggregations": {
                "projects": {
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
        self.request.side_effect = [resp]

    def setUp(self):
        super(RegionsTestCase, self).setUp()
        self._mock_response()

    def test_get_health(self):

        resp = self.client.get("/api/v1/health/")
        resp_json = json.loads(resp.data.decode())
        self.assertEqual(200, resp.status_code)
        self.assertEqual(set(self.services), set(resp_json["project_names"]))
        self.assertEqual(set(self.services), set(resp_json["projects"].keys()))

        request_args, request_kwargs = self.request.call_args
        self.assertEqual(
            ("get", self.app.config["backend"]["elastic"] + "/_search"),
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

    def test_get_health_region(self):

        resp = self.client.get("/api/v1/health/regionX")
        self.assertEqual(200, resp.status_code)

        request_args, request_kwargs = self.request.call_args
        self.assertEqual(
            ("get", self.app.config["backend"]["elastic"] + "/_search"),
            request_args)
        data_requested = json.loads(request_kwargs["data"])
        expected_filter = [{
            "range": {
                "timestamp": {
                    "gte": "now-1d/m"
                }
            }
        }, {
            "match": {"region": "regionX"}
        }]
        self.assertEqual(expected_filter,
                         data_requested["query"]["bool"]["filter"])

    def test_get_health_period(self):

        resp = self.client.get("/api/v1/health/?period=year")
        self.assertEqual(200, resp.status_code)

        request_args, request_kwargs = self.request.call_args
        self.assertEqual(
            ("get", self.app.config["backend"]["elastic"] + "/_search"),
            request_args)
        data_requested = json.loads(request_kwargs["data"])
        expected_filter = [{
            "range": {
                "timestamp": {
                    "gte": "now-365d/m"
                }
            }
        }]
        self.assertEqual(expected_filter,
                         data_requested["query"]["bool"]["filter"])
