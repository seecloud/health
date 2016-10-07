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
from tests.unit import test


class InitElasticTestCase(test.TestCase):
    def setUp(self):
        super(InitElasticTestCase, self).setUp()
        self.request = self.mock_request()

    def test_existen_index(self):
        self.request.return_value.status_code = 200
        es.init_elastic('fake-es')
        self.request.assert_called_once_with('get', 'fake-es/ms_health',
                                             allow_redirects=True, params=None)

    def test_create_index(self):
        self.request.side_effect = (mock.Mock(status_code=404),
                                    mock.Mock(status_code=200))
        es.init_elastic('fake-es', index_to_create='fake-index')
        calls = [mock.call('get', 'fake-es/ms_health', allow_redirects=True,
                           params=None),
                 mock.call('post', 'fake-es/fake-index', data=mock.ANY,
                           json=None)]
        self.assertEqual(2, self.request.call_count)
        self.request.assert_has_calls(calls)
