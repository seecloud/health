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
import os.path

import mock
import testtools

import health.main


class APITestCase(testtools.TestCase):

    def setUp(self):
        super(APITestCase, self).setUp()
        self.addCleanup(mock.patch.stopall)
        self.client = health.main.app.test_client()
        self.app = health.main.app

        config_path = os.path.join(
            os.path.dirname(__file__), 'etc/config.json')
        config = json.load(open(config_path))
        self.app.config.update(config)

        self.request = mock.patch("requests.api.request").start()

    def test_not_found(self):
        resp = self.client.get('/404')
        self.assertEqual({"error": "Not Found"},
                         json.loads(resp.data.decode()))
        self.assertEqual(404, resp.status_code)
