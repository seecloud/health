Cloud Health
============


Collects all required data for Health Dashboard and stores it to ES for future use.


health/
-------

All project scripts and code is inside this directory


health/es_init.sh
~~~~~~~~~~~~~~~~~

Contains code that initializes ElasticSearch:
* Adds index "ms_health_idx_1"
* Adds alias "ms_health" -> "ms_health_idx_1"
* Set's "ms_health_idx_1" mapping as in file es_health_index.json



extra/*
-------

Useful scripts and data that were developed during the development.
