#!/usr/bin/env bash

if [ -f pid ]; then
    bash stop.bash
fi

echo "Starting CV Extractor App"

gunicorn cv_extractor_app_wsgi:app \
	-p ./pid \
	-k eventlet \
	-b 0.0.0.0:5000 \
	--name=cv_extractor_app \
	--workers 1 \
	--log-level 0 \
	--log-file logs/cv_extractor_app.log \
	--error-logfile logs/cv_extractor_app.error.log \
	--access-logfile logs/cv_extractor_app.access.log \
	--capture-output \
	--reload
sleep 1
if [ -f pid ]; then
    echo "	started master worker pid:$(cat pid)"
else
	echo "	failed starting master worker"
fi
