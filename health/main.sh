#!/bin/bash

LOG=/var/log/health

touch $LOG

if [ ! -z "$RUN_HEALTH_JOB" ]; then
    python job.py >> $LOG &
fi

if [ ! -z "$RUN_HEALT_API" ]; then
    gunicorn -w 4 -b 0.0.0.0:5000 main:app >> $LOG &
fi

tail -f $LOG
