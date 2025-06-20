#!/bin/sh
echo
echo "Waiting for Mongodb..."

while ! nc -z mongodb 27017; do
  sleep 0.3
done

echo
echo
echo "!!! mongodb started !!!"

exec "$@"


echo
echo "Waiting for Redis..."

while ! nc -z redis 6379; do
  sleep 0.3
done

echo
echo
echo "!!! redis started !!!"

exec "$@"


echo
echo "##################################"
echo "##################################"
echo "######## Simpliance Server #######"
echo "##################################"
echo "##################################"
echo

echo
echo "!! Start up with 2 workers for distributed ability !!"
echo

exec gunicorn --bind 0.0.0.0:8000 main:app -k uvicorn.workers.UvicornWorker --workers 2 --log-level warning