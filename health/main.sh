#!/bin/bash

LOG=/var/log/health

touch $LOG

if [ ! -z "$RUN_HEALTH_JOB" ]; then
    health-job >> $LOG &
fi

if [ ! -z "$RUN_HEALT_API" ]; then
    gunicorn -w 4 -b 0.0.0.0:5000 health.main:app >> $LOG &
fi

tail -f $LOG
