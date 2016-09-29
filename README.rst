Cloud Health
============


.. image:: https://coveralls.io/repos/github/seecloud/health/badge.svg?branch=master
    :target: https://coveralls.io/github/seecloud/health?branch=master

.. image:: https://travis-ci.org/seecloud/health.svg?branch=master
    :target: https://travis-ci.org/seecloud/health

Collects all required data for Health Dashboard and stores it to ES for future use.


How To Use & Run
----------------

Build Docker Image
~~~~~~~~~~~~~~~~~~

.. code-block:: sh

    docker run -d --name health-app -v ~/health/etc:/etc/health -p 6000:5000 health


Run Docker Container
~~~~~~~~~~~~~~~~~~~~


.. code-block:: sh

    # Update ~/health/etc/config.json file to match your configuration
    vi ~/health/etc/config.json
    # Run container
    docker run -d --name health-app -v ~/health/etc:/etc/health -p 6000:5000 health


Get App Logs
~~~~~~~~~~~~

.. code-block:: sh

    docker logs health-app
