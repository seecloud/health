Sample of Config File For Health Data Collector
===============================================

Configs? Why?
-------------

Health project works in next way:

1) It collects data from every specified region, aggregates them and store
in own backend
2) Every region can have own way to store data, that's why for each region
we are specifying driver with it's own arguments that should return data
in very standardize way.

So to make this work we need to specify:
1) All regions and their drivers
2) Drivers arguments
3) Backend arguments
4) How often to run job that syncs everything


Placement
---------

Update ``config.json`` file and place it in /etc/health/ directory.
If you run docker container with health the best way is to mount volume
to /etc/health that contains config.json file.
