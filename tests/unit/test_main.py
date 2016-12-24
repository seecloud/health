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
import testtools

from health import main


class MainTestCase(testtools.TestCase):
    @mock.patch("oss_lib.config.CONF", new_callable=dict)
    @mock.patch("health.main.argparse.ArgumentParser")
    @mock.patch("oss_lib.config.process_args")
    @mock.patch("health.app.app")
    def test_main(self, mock_app, mock_process, mock_parser, mock_conf):
        mock_process.return_value.configure_mock(
            host="0.0.0.0",
            port=5000,
            debug=False,
        )
        main.main()
        mock_app.config.update.assert_called_once_with({}, **{"DEBUG": False})
        mock_app.run.assert_called_once_with(host="0.0.0.0", port=5000)
