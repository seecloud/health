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
import logging
import os

import flask
from flask_helpers import routing  # noqa

from health.api.v1 import health
from health.api.v1 import regions


CONF = None
DEFAULT_CONF = {
    "flask": {
        "PORT": 5000,
        "HOST": "0.0.0.0",
        "DEBUG": True
    }
}


if not CONF:
    path = os.environ.get("HEALTH_CONF", "/etc/health/config.json")
    try:
        CONF = json.load(open(path))
        logging.info("Config is '%s'" % path)
    except IOError as e:
        logging.warning("Config at '%s': %s" % (path, e))
        CONF = DEFAULT_CONF

APP_CONF = CONF["flask"]


app = flask.Flask(__name__, static_folder=None)
app.config.update(APP_CONF)


@app.errorhandler(404)
def not_found(error):
    return flask.jsonify({"error": "Not Found"}), 404


for bp in [health, regions]:
    for url_prefix, blueprint in bp.get_blueprints():
        app.register_blueprint(blueprint, url_prefix="/api/v1%s" % url_prefix)


app = routing.add_routing_map(app, html_uri=None, json_uri="/api/v1")


def main():
    app.run(host=APP_CONF["HOST"],
            port=APP_CONF["PORT"])


if __name__ == "__main__":
    main()
