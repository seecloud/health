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

import mock

from health import job
from tests.unit import test


class JobTestCase(test.ConfigFixtureMixin, test.TestCase):
    def setUp(self):
        super(JobTestCase, self).setUp()
        # Setup configuration for tests
        self.setup_config_fixture()

        # ensure json.dumps produces predictable results
        dumps_with_sorting = functools.partial(json.dumps, sort_keys=True)
        patcher = mock.patch("json.dumps", new=dumps_with_sorting)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_exceptions_decorator(self):
        self.assertTrue(job.ignore_exceptions(lambda: True)())

        @job.ignore_exceptions
        def raisesException():
            raise ValueError

        self.assertIsNone(raisesException())

    @mock.patch("health.drivers.tcp.driver.Driver.fetch")
    @mock.patch("requests.api.request")
    def test_job(self, mock_request, mock_driver_fetch):
        mock_driver_fetch.return_value = [[{"fake1": "fake1"}],
                                          [],
                                          [{"fake2": "fake2"}]]
        job.job()
        self.assertEqual(4, mock_request.call_count)
        expected_calls = [
            mock.call("post",
                      "http://4.3.2.1:9200/"
                      "/ms_health_hooli-west-1/service/_bulk",
                      data='{"index": {}}\n'
                           '{"fake1": "fake1", "region": "hooli-west-1"}',
                      json=None),
            mock.call("post",
                      "http://4.3.2.1:9200/"
                      "/ms_health_hooli-west-1/service/_bulk",
                      data='{"index": {}}\n'
                           '{"fake2": "fake2", "region": "hooli-west-1"}',
                      json=None)
        ]
        self.assertEqual(expected_calls, mock_request.call_args_list[2:])
