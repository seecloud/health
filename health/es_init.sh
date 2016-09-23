#!/usr/bin/env bash

echo "Initializing ElasticSearch for Health dashboard"

index_exists=`curl -s -o /dev/null -w "%{http_code}" -XGET $1/ms_health`
exists_code="200"

if  [ "$index_exists" -eq "$exists_code" ];
    then
        echo "Index already exists, nothing to do."
        echo "Finished"
    else
        curl --data "@./es_health_index.json" -XPOST $1/ms_health_idx_1
        echo
        echo "Index was created successfully"
        echo "Finished"
fi
