Directory With Scripts That Are Related To This Project
=======================================================


shapshot_es_index.py
--------------------

Allows you to snapshot indexes.


Usage
~~~~~

Just run this command:

.. code-block:: sh
    ES="http://172.16.5.147:9200" INDEXES="log" BACKUP_PATH="/mount/es_backup/logs" python snapshot_es_index.py


If you need to debug use DEBUG=True env variable

.. code-block:: sh
    DEBUG=True [....] python shanpshot_es_index.py



Arguments
~~~~~~~~~

* *ES* - ElasticSearch connection string
* *INDEXES* - list of INDEXES that should be backed up
* *REPO_PATH* Full path to backup directory in ES. It's configure in
*elasticsearch.yml* in *path.repo* option
* *REPO_NAME* Name of backup, all it's data will be store in <REPO_PATH>/<REPO_NAME>
* *DEBUG* Print exception or not

