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

from health.mapping import es
from tests.unit import test  # noqa


class InitElasticTestCase(test.TestCase):

    def setUp(self):
        super(InitElasticTestCase, self).setUp()
        es.existing_indices = set()

    @mock.patch("requests.api.request")
    def test_init_elastic_index_exists(self, mock_request):
        mock_request.return_value.status_code = 200
        mock_request.return_value.ok = True
        es.ensure_index_exists("fake-es", "regionOne")
        self.assertEqual(1, mock_request.call_count)
        calls = [mock.call("get", "fake-es/ms_health_regionOne",
                           allow_redirects=True, params=None)]

        mock_request.assert_has_calls(calls)

    @mock.patch("requests.api.request")
    def test_init_elastic_create_index(self, mock_request):
        mock_request.side_effect = [
            mock.Mock(status_code=404, ok=False),
            mock.Mock(status_code=200, ok=True)
        ]
        es.ensure_index_exists("fake-es", "regionOne")
        calls = [mock.call("get", "fake-es/ms_health_regionOne",
                           allow_redirects=True, params=None),
                 mock.call("put", "fake-es/ms_health_regionOne",
                           data=mock.ANY)]
        self.assertEqual(2, mock_request.call_count)
        mock_request.assert_has_calls(calls)

    @mock.patch("health.mapping.es.sys")
    @mock.patch("requests.api.request")
    def test_init_elastic_exit_if_failed(self, mock_request, mock_sys):
        mock_request.side_effect = [
            mock.Mock(status_code=404, ok=False),
            mock.Mock(status_code=400, ok=False)
        ]

        es.ensure_index_exists("fake-es", "regionOne")
        self.assertEqual(2, mock_request.call_count)
        mock_sys.exit.assert_called_once_with(1)
