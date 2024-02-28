#!/usr/bin/env bash

source venv/bin/activate

echo "Starting Custom Job App"

gunicorn custom_job_app_wsgi:app \
	-p ./pid \
	-k eventlet \
	-b 0.0.0.0:5000 \
	--name=custom_job_app \
	--workers 1 \
	--log-level 0 \
	--log-file logs/custom_job_app.log \
	--error-logfile logs/custom_job_app.error.log \
	--access-logfile logs/custom_job_app.access.log \
	--capture-output \
	--reload
sleep 1
if [ -f pid ]; then
    echo "	started master worker pid:$(cat pid)"
else
	echo "	failed starting master worker"
fi
