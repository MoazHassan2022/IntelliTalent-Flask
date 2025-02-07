#!/usr/bin/env bash

if [ -f pid ]; then
    bash stop.bash
fi

echo "Starting Quiz App"

gunicorn quiz_app_wsgi:app \
	-p ./pid \
	-k eventlet \
	-b 0.0.0.0:5000 \
	--name=quiz_app \
	--workers 4 \
	--log-level 0 \
	--log-file logs/quiz_app.log \
	--error-logfile logs/quiz_app.error.log \
	--access-logfile logs/quiz_app.access.log \
	--capture-output \
	--daemon
sleep 1
if [ -f pid ]; then
	echo "	started master worker pid:$(cat pid)"
else
	echo "	failed starting master worker"
fi
