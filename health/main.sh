#!/bin/bash

if [ ! -z "$RUN_HEALTH_JOB" ]; then
    health-job &
fi

if [ ! -z "$RUN_HEALTH_API" ]; then
    gunicorn -w 4 -b 0.0.0.0:5000 health.wsgi &
fi

wait -n
