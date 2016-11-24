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

import functools
import json
import os

import mock

from health import job as main
import tests
from tests.unit import test  # noqa

TEST_CONFIG_PATH = os.path.join(os.path.dirname(tests.__file__), "..",
                                "etc", "config.json")


class JobTestCase(test.TestCase):
    def setUp(self):
        super(JobTestCase, self).setUp()
        with open(TEST_CONFIG_PATH) as f:
            test_conf = json.load(f)
        mock.patch("health.job.CONF", test_conf).start()
        self.request = self.mock_request()

        # ensure json.dumps produces predictable results
        self.old_dumps = json.dumps
        json.dumps = functools.partial(json.dumps, sort_keys=True)

    def tearDown(self):
        super(JobTestCase, self).tearDown()
        json.dumps = self.old_dumps

    @mock.patch("health.drivers.tcp.driver.main")
    def test_job(self, mock_driver_main):
        mock_driver_main.return_value = [[{"fake1": "fake1"}],
                                         [],
                                         [{"fake2": "fake2"}]]
        main.job()
        self.assertEqual(4, self.request.call_count)
        expected_calls = [
            mock.call("post",
                      "http://4.3.2.1:9200//ms_health/service/_bulk",
                      data='{"index": {}}\n'
                           '{"fake1": "fake1", "region": "hooli-west-1"}',
                      json=None),
            mock.call("post",
                      "http://4.3.2.1:9200//ms_health/service/_bulk",
                      data='{"index": {}}\n'
                           '{"fake2": "fake2", "region": "hooli-west-1"}',
                      json=None)
        ]
        self.assertEqual(expected_calls, self.request.call_args_list[2:])
