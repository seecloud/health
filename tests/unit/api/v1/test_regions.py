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

    @mock.patch("requests.api.request")
    def test_get_regions(self, mock_request):
        sample_response = {
            "regionOne": mock.ANY,
            "regionTwo": mock.ANY,
            "regionThree": mock.ANY,
        }
        regions = set(["regionOne", "regionTwo", "regionThree"])
        sample_response = {"ms_health_" + reg_name for reg_name in regions}

        resp = mock.Mock()
        resp.json.return_value = sample_response
        mock_request.side_effect = [resp]

        resp = self.client.get("/api/v1/regions/")
        resp_json = json.loads(resp.data.decode())
        self.assertEqual(set(regions), set(resp_json))
        self.assertEqual(200, resp.status_code)
