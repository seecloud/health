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
import os

import jsonschema
import mock

from health import main
import tests
from tests.unit import test

TEST_CONFIG_PATH = os.path.join(os.path.dirname(tests.__file__), '..',
                                'etc', 'config.json')


class JobTestCase(test.TestCase):
    def setUp(self):
        super(JobTestCase, self).setUp()
        with open(TEST_CONFIG_PATH) as f:
            test_conf = json.load(f)
        mock.patch('health.main.CONF', test_conf).start()
        self.request = self.mock_request()

    @mock.patch('health.drivers.tcp.driver.main')
    def test_job(self, mock_driver_main):
        mock_driver_main.return_value = [[{'fake1': 'fake1'}],
                                         [],
                                         [{'fake2': 'fake2'}]]
        main.job()
        self.assertEqual(4, self.request.call_count)
        expected_calls = [
            mock.call('post',
                      'http://4.3.2.1:9200//ms_health/service/_bulk',
                      data='{"index": {}}\n'
                           '{"region": "hooli-west-1", "fake1": "fake1"}',
                      json=None),
            mock.call('post',
                      'http://4.3.2.1:9200//ms_health/service/_bulk',
                      data='{"index": {}}\n'
                           '{"region": "hooli-west-1", "fake2": "fake2"}',
                      json=None)
        ]
        self.assertEqual(expected_calls, self.request.call_args_list[2:])


class StopException(RuntimeError):
    pass


class MainTestCase(test.TestCase):
    def setUp(self):
        super(MainTestCase, self).setUp()
        self.mock_argv(TEST_CONFIG_PATH)

    def mock_argv(self, config_path):
        mock.patch('sys.argv', ['test-health-prog', '--config-path',
                                config_path]).start()

    @staticmethod
    def mock_open(read_data='[]'):
        return mock.patch('%s.open' % main.__name__,
                          mock.mock_open(read_data=read_data)).start()

    def test_main_invalid_config_file(self):
        self.mock_argv('fake.json')
        self.assertRaises(IOError, main.main)

    def test_main_incorrect_config(self):
        self.mock_open()
        self.assertRaises(jsonschema.ValidationError, main.main)

    @mock.patch('health.main.CONF_SCHEMA', {"type": "fake-object"})
    def test_main_incorrect_schema(self):
        self.mock_open()
        self.assertRaises(jsonschema.SchemaError, main.main)

    @mock.patch('health.main.job')
    @mock.patch('time.sleep', side_effect=[True, StopException])
    def test_main(self, mock_sleep, mock_job):
        self.mock_request()
        self.assertRaises(StopException, main.main)
        mock_job.assert_called_once()
        self.assertEqual(2, mock_sleep.call_count)
